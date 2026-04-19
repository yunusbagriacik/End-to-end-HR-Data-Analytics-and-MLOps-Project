def get_department_market_risk(department_name: str) -> float:
    mapping = {
        "Sales": 0.8,
        "Technology": 0.4,
        "HR": 0.5,
        "Finance": 0.6,
        "Operations": 0.7,
    }
    return mapping.get(department_name, 0.5)