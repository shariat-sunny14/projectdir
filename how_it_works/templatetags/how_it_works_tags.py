from django import template

from how_it_works.models import ProcessSection, ProcessStep

register = template.Library()


@register.inclusion_tag("how_it_works/process_section.html")
def render_process_section():
    """
    Homepage টেমপ্লেটে এভাবে ব্যবহার করুন:

        {% load how_it_works_tags %}
        {% render_process_section %}
    """
    section = ProcessSection.load()
    steps = ProcessStep.objects.filter(is_active=True).order_by("order", "step_number")
    return {"process_section": section, "process_steps": steps}
