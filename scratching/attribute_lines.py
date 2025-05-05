from scratching.app import run
import barcode

def execute(env):
    product = env['product.template'].search([('default_code', '=', '15606')])
    attribute_lines = env['product.template.attribute.line'].search([('id', 'in', product.attribute_line_ids.ids)])
    for line in attribute_lines:
        attribute_values = env['product.attribute.value'].search([('id', 'in', line.value_ids.ids)])
        attribute_value_list = [at.name for at in attribute_values]
        print(f"{line.attribute_id.name}: {attribute_value_list}")



if __name__ == '__main__':
    run(execute, commit_changes=False)