from django import template

register = template.Library()

@register.filter(name='replace_slash')
def replace_slash(value, field_name):
    """Replace slashes with hyphens in the specified field."""
    return getattr(value, field_name).replace("/", "-")

@register.filter
def get_item(dictionary, key):
    """Safely get a value from a dictionary, handling NoneType errors."""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None

@register.filter
def get_color(status):
    """ แปลงสถานะเป็นสี background """
    if status == "on_time":
        return "#16a34a"  # สีเขียว
    elif status == "late":
        return "#facc15"  # สีเหลือง
    elif status == "absent":
        return "#dc2626"  # สีแดง
    return "#d1d5db"  # สีเทา

@register.filter
def get_item(dictionary, key):
    """ ฟิลเตอร์เพื่อเข้าถึงค่าใน dictionary โดยใช้ key """
    try:
        return dictionary.get(key)
    except (KeyError, TypeError):
        return None
    
@register.filter
def dict_key(d, key):
    """ ดึงค่าจาก dictionary โดยใช้ key """
    return d.get(key, None) if isinstance(d, dict) else None