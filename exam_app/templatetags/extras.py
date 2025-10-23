from django import template

register = template.Library()

@register.filter
def lookup(d, key):
    """ดึงค่าจาก dict ด้วย key:  attendance_dict|lookup:student.id"""
    try:
        return d.get(key)
    except Exception:
        return None
