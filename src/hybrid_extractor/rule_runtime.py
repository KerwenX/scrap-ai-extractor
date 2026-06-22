from __future__ import annotations

import re
from typing import Any, Callable

from bs4 import BeautifulSoup

from .models import ExtractionPlan, ExtractionResult, FieldEvidence, FieldRule
from .preprocessing import extract_page_description, normalize_text


CodeRuleHandler = Callable[[BeautifulSoup, FieldRule], Any]


class RuleRuntime:
    def __init__(self, code_handlers: dict[str, CodeRuleHandler] | None = None) -> None:
        self.code_handlers = code_handlers or {}

    def execute(self, soup: BeautifulSoup, plan: ExtractionPlan) -> ExtractionResult:
        data: dict[str, Any] = {}
        evidences: list[FieldEvidence] = []

        for field_rule in plan.fields:
            value = None
            source = ""
            rule_id = None

            for selector in field_rule.selectors:
                value = self._resolve_selector(soup, selector)
                if self._has_value(value):
                    source = f"{selector.kind}:{selector.value}"
                    rule_id = f"{field_rule.field_name}:{selector.kind}"
                    break

            if not self._has_value(value):
                value = field_rule.fallback_value

            value = self._apply_postprocess(value, field_rule)
            data[field_rule.field_name] = value
            if field_rule.merge_output and isinstance(value, dict):
                self._merge_mapping(data, value)
            if self._has_value(value):
                evidences.append(
                    FieldEvidence(field_name=field_rule.field_name, source=source, rule_id=rule_id)
                )

        return ExtractionResult(data=data, evidences=evidences)

    def _resolve_selector(self, soup: BeautifulSoup, selector) -> Any:
        if selector.kind == "css":
            nodes = soup.select(selector.value)
            return self._extract_nodes(nodes, selector.attr, selector.many)

        if selector.kind == "id":
            node = soup.find(id=selector.value)
            if not node:
                return None
            return self._extract_nodes([node], selector.attr, selector.many)

        if selector.kind == "meta":
            if selector.value == "description":
                return extract_page_description(soup)
            node = soup.find("meta", attrs={"name": selector.value})
            return node.get("content", "") if node else None

        if selector.kind == "text_pattern":
            text = normalize_text(soup.get_text("\n", strip=True))
            match = re.search(selector.value, text)
            if not match:
                return None
            if match.groups():
                return match.group(1)
            return match.group(0)

        if selector.kind == "section_tab":
            tab_map = self._build_section_tab_map(soup)
            return tab_map.get(selector.value)

        if selector.kind == "label_value":
            return self._extract_label_value(soup, selector.value, selector.many)

        if selector.kind == "all_label_values":
            return self._extract_all_label_values(soup)

        if selector.kind == "all_sections":
            return self._extract_all_sections(soup)

        if selector.kind == "code":
            handler = self.code_handlers.get(selector.value)
            if not handler:
                return None
            return handler(soup, selector)

        return None

    def _build_section_tab_map(self, soup: BeautifulSoup) -> dict[str, str]:
        tabs = [
            normalize_text(node.get_text())
            for node in soup.select(".van-tabs__nav [role='tab'] .van-tab__text")
            if normalize_text(node.get_text())
        ]
        panes = soup.select(".van-tab__pane-wrapper .van-tab__pane")
        result: dict[str, str] = {}
        for tab, pane in zip(tabs, panes):
            result[tab] = normalize_text(pane.get_text("\n", strip=True))
        return result

    def _extract_nodes(self, nodes, attr: str, many: bool) -> Any:
        values = []
        for node in nodes:
            if attr == "text":
                value = normalize_text(node.get_text(" ", strip=True))
            else:
                value = normalize_text(node.get(attr, "")) if node.get(attr) else ""
            if value:
                values.append(value)
        if many:
            return values
        return values[0] if values else None

    def _extract_label_value(self, soup: BeautifulSoup, label: str, many: bool) -> Any:
        normalized_label = normalize_text(label)
        if not normalized_label:
            return None

        values: list[str] = []

        # Pattern: <div class="item-container"><div class="item-title-container">标签</div><span class="item-content">值</span></div>
        for container in soup.select(".item-container"):
            title_node = container.select_one(".item-title-container")
            value_node = container.select_one(".item-content")
            if not title_node or not value_node:
                continue
            title_text = normalize_text(title_node.get_text(" ", strip=True)).replace(" ", "")
            if title_text != normalized_label.replace(" ", ""):
                continue
            extracted = normalize_text(value_node.get_text(" ", strip=True))
            if extracted:
                values.append(extracted)

        if values:
            unique_values = []
            seen = set()
            for value in values:
                if value in seen:
                    continue
                seen.add(value)
                unique_values.append(value)
            if many:
                return unique_values
            return unique_values[0]

        for node in soup.find_all(["td", "th", "dt", "dd", "span", "div", "label", "strong", "b"]):
            node_text = normalize_text(node.get_text(" ", strip=True))
            if node_text != normalized_label:
                continue

            extracted = self._extract_value_near_label(node)
            if not extracted:
                continue
            values.append(extracted)

        unique_values = []
        seen = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique_values.append(value)

        if many:
            return unique_values
        return unique_values[0] if unique_values else None

    def _extract_all_label_values(self, soup: BeautifulSoup) -> dict[str, str]:
        results: dict[str, str] = {}

        for container in soup.select(".item-container"):
            title_node = container.select_one(".item-title-container")
            value_node = container.select_one(".item-content")
            if not title_node or not value_node:
                continue
            title = normalize_text(title_node.get_text(" ", strip=True)).replace(" ", "")
            value = normalize_text(value_node.get_text(" ", strip=True))
            if title and value and title not in results:
                results[title] = value

        for row in soup.select("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) < 2:
                continue
            label = normalize_text(cells[0].get_text(" ", strip=True)).rstrip(":：")
            value = normalize_text(cells[1].get_text(" ", strip=True))
            if label and value and label not in results:
                results[label] = value

        for dl in soup.select("dl"):
            terms = dl.find_all("dt", recursive=False)
            descriptions = dl.find_all("dd", recursive=False)
            for term, description in zip(terms, descriptions):
                label = normalize_text(term.get_text(" ", strip=True)).rstrip(":：")
                value = normalize_text(description.get_text(" ", strip=True))
                if label and value and label not in results:
                    results[label] = value

        return results

    def _extract_all_sections(self, soup: BeautifulSoup) -> dict[str, str]:
        results: dict[str, str] = {}

        for container in soup.select(".public-container"):
            title = self._extract_container_title(container)
            content = self._extract_container_content(container)
            if title and content and title not in results:
                results[title] = content

        if results:
            return results

        for container in soup.select("section, article, .section, .content-section"):
            title = self._extract_container_title(container)
            content = self._extract_container_content(container)
            if title and content and title not in results:
                results[title] = content

        return results

    def _extract_value_near_label(self, node) -> str | None:
        next_sibling = self._next_element_sibling(node)
        if next_sibling:
            value = normalize_text(next_sibling.get_text(" ", strip=True))
            if value:
                return value

        parent = node.parent
        if parent:
            parent_children = [child for child in parent.find_all(recursive=False) if getattr(child, "name", None)]
            if len(parent_children) >= 2:
                try:
                    index = parent_children.index(node)
                except ValueError:
                    index = -1
                if 0 <= index < len(parent_children) - 1:
                    value = normalize_text(parent_children[index + 1].get_text(" ", strip=True))
                    if value:
                        return value
                if index == len(parent_children) - 1 and index > 0:
                    value = normalize_text(parent_children[index].get_text(" ", strip=True))
                    label = normalize_text(parent_children[index - 1].get_text(" ", strip=True))
                    if value and label:
                        return value

        return None

    def _next_element_sibling(self, node):
        sibling = node.next_sibling
        while sibling is not None and not getattr(sibling, "name", None):
            sibling = sibling.next_sibling
        return sibling

    def _extract_container_title(self, node) -> str:
        title_node = node.select_one(
            "h2, h3, h4, .section-title, .title, .item-title, .title-line p, .title p"
        )
        if not title_node:
            return ""
        return normalize_text(title_node.get_text(" ", strip=True))

    def _extract_container_content(self, node) -> str:
        content_node = node.select_one(".item-content, .content, .section-content")
        target = content_node or node
        return normalize_text(target.get_text("\n", strip=True))

    def _merge_mapping(self, data: dict[str, Any], mapping: dict[str, Any]) -> None:
        for key, value in mapping.items():
            if not key or not self._has_value(value):
                continue
            existing = data.get(key)
            if not self._has_value(existing):
                data[key] = value

    def _apply_postprocess(self, value: Any, field_rule: FieldRule) -> Any:
        current = value
        for step in field_rule.postprocess:
            current = self._apply_step(current, step.op, step.args)
        return current

    def _apply_step(self, value: Any, op: str, args: dict[str, Any]) -> Any:
        if value is None:
            return None

        if op == "strip":
            if isinstance(value, str):
                return value.strip()
            if isinstance(value, list):
                return [item.strip() for item in value if isinstance(item, str)]

        if op == "strip_cn_punctuation":
            if isinstance(value, str):
                return value.strip("，。；：: ")
            if isinstance(value, list):
                return [item.strip("，。；：: ") for item in value if isinstance(item, str)]

        if op == "split_cn_list":
            if isinstance(value, str):
                normalized = (
                    value.replace("、", "，")
                    .replace("以及", "，")
                    .replace("及", "，")
                    .replace("等", "")
                )
                return [item.strip("，。 ") for item in normalized.split("，") if item.strip("，。 ")]

        if op == "unique":
            if isinstance(value, list):
                result = []
                seen = set()
                for item in value:
                    key = str(item)
                    if key in seen:
                        continue
                    seen.add(key)
                    result.append(item)
                return result

        if op == "first_non_empty_line":
            if isinstance(value, str):
                for line in value.splitlines():
                    line = normalize_text(line)
                    if line:
                        return line
                return ""

        if op == "regex_extract":
            pattern = str(args.get("pattern", "")).strip()
            group = int(args.get("group", 1))
            if pattern and isinstance(value, str):
                match = re.search(pattern, value)
                if not match:
                    return None
                if match.groups():
                    try:
                        return match.group(group)
                    except IndexError:
                        return match.group(0)
                return match.group(0)

        if op == "regex_replace":
            pattern = str(args.get("pattern", "")).strip()
            repl = str(args.get("repl", ""))
            if pattern and isinstance(value, str):
                return re.sub(pattern, repl, value)
            if pattern and isinstance(value, list):
                return [re.sub(pattern, repl, item) if isinstance(item, str) else item for item in value]

        if op == "join":
            separator = str(args.get("separator", ", "))
            if isinstance(value, list):
                return separator.join(str(item) for item in value if self._has_value(item))

        if op == "filter_empty":
            if isinstance(value, list):
                return [item for item in value if self._has_value(item)]

        if op == "normalize_whitespace":
            if isinstance(value, str):
                return normalize_text(value)
            if isinstance(value, list):
                return [normalize_text(item) if isinstance(item, str) else item for item in value]

        if op == "to_int":
            if isinstance(value, str):
                match = re.search(r"-?\d+", value.replace(",", ""))
                if match:
                    return int(match.group(0))
            if isinstance(value, (int, float)):
                return int(value)

        if op == "to_float":
            if isinstance(value, str):
                match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
                if match:
                    return float(match.group(0))
            if isinstance(value, (int, float)):
                return float(value)

        return value

    def _has_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, dict, set)):
            return len(value) > 0
        return True
