def auto_assign_department(category: str):
    mapping = {
        "pothole": "Public Works",
        "streetlight": "Electricity",
        "trash": "Sanitation",
        "water": "Water Dept",
        "police": "Police",
        "ambulance": "Health/Emergency",
        "default": "General"
    }
    if not category:
        return mapping["default"]
    return mapping.get(category.lower(), mapping["default"])