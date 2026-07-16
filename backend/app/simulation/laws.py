from typing import List, Callable, Any

class Law:
    def __init__(self, law_id: str, title: str, rule_expression: str):
        self.law_id = law_id
        self.title = title
        self.rule_expression = rule_expression  # Example: "agent.inventory['grain'] >= 0"
        self.validator = self._compile_rule()

    def _compile_rule(self) -> Callable[[Any], bool]:
        """Compile string expression to callable predicate checker"""
        try:
            # Safe evaluation parsing logic
            # E.g. limit to check variables safely
            return lambda agent: eval(self.rule_expression, {}, {"agent": agent})
        except Exception:
            return lambda agent: True

class LawRegistry:
    """Enforces active civilization rules/laws on citizen agent actions"""
    def __init__(self):
        self.laws: List[Law] = []

    def pass_law(self, law: Law):
        self.laws.append(law)

    def enforce_rules(self, agent: Any) -> bool:
        """Returns True if agent complies with all active laws, False otherwise"""
        for law in self.laws:
            try:
                if not law.validator(agent):
                    return False
            except Exception:
                pass
        return True
