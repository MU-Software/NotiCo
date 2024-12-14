import jinja2
import jinja2.meta
import jinja2.nodes


def get_template_variables(template_str: str, template_variable_start_end_string: tuple[str, str]) -> set[str]:
    # From https://stackoverflow.com/a/77363330
    return jinja2.meta.find_undeclared_variables(
        ast=jinja2.Environment(
            autoescape=True,
            variable_start_string=template_variable_start_end_string[0],
            variable_end_string=template_variable_start_end_string[1],
        ).parse(source=template_str)
    )
