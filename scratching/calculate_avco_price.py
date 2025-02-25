from scratching.app import run
from prettytable import PrettyTable  # Use this to display a table in the console

from datetime import datetime


def get_direction(source, destination):
    if source.usage == 'internal' and destination.usage == 'internal':
        return 'neutral'
    elif source.usage == 'internal' and destination.usage == 'customer':
        return 'outgoing'
    elif source.usage == 'customer' and destination.usage == 'internal':
        return 'incoming'
    elif source.usage == 'inventory' and destination.usage == 'internal':
        return 'neutral'
    elif source.usage == 'supplier' and destination.usage == 'internal':
        return 'incoming'
    elif source.usage == 'inventory' or destination.usage == 'inventory':
        return 'neutral'
    elif source.usage == 'internal' or destination.usage == 'supplier':
        return 'outgoing'
    elif source.usage == 'internal' or destination.usage == 'transit':
        return 'outgoing'
    else:
        raise Exception(f'Unknown direction {source.display_name}, {destination.display_name}')

def get_stock(env, product):
    stores = env["store.store"].sudo().search([])
    qty = 0

    for store in stores:
        quantities = (
            product.product_variant_id.with_context(location=store.stock_location_id.id)
            .sudo()
            ._compute_quantities_dict(
                lot_id=False,
                owner_id=False,
                package_id=False,
                from_date=False,
                to_date=False
            )
        )
        qty += quantities.get('qty_available', 0)

    return qty

def execute(env):

    category_ids = {76, 75, 73, 93}
    categories = env['product.category'].browse(category_ids)
    products = env['product.template'].search([('categ_id', 'in', categories.ids)])

    [print(product.display_name) for product in products]


    products = env['product.template'].search([('default_code', '=', '14390')])

    data = {}
    for product in products:
        result = calculate(env, product)
        data[result['product'].default_code] = result

        print(f"{result['product'].display_name}, {result['avco_price']}")

    table = PrettyTable()
    table.field_names = ["Product", "Avco Price"]

    for key, value in data.items():
        table.add_row([
            value["product"].display_name,
            value["avco_price"],
        ])

    table.align['Product'] = 'l'
    table.align['Avco Price'] = 'r'

    print(data['14390']['table'])


def calculate(env, product):
    all_account_moves = env['account.move'].search([('line_ids.product_id', '=', product.product_variant_id.id)])
    all_stock_moves = env['stock.move'].search([('move_line_ids.product_id', '=', product.product_variant_id.id)])

    def prepare(item, data, field):
        moves = []
        for move in data:
            lines = move[field].filtered(lambda m: m.product_id.id == item.product_variant_id.id)
            moves.append((move, lines))
        return moves

    account_moves = prepare(product, all_account_moves, 'line_ids')
    stock_moves = prepare(product, all_stock_moves, 'move_line_ids')

    # Collect all rows in a list
    rows = []

    for move, lines in account_moves:
        for line in lines:
            # Normalize date to datetime
            normalized_date = line.date if isinstance(line.date, datetime) else datetime.combine(line.date, datetime.min.time())
            rows.append({
                "date": normalized_date,
                "record_type": "account_move",
                "name": move.display_name,
                "id": f"{line.move_id.id}/{line.id}",
                "price_unit": line.price_unit,
                "source_location": "",
                "destination_location": "",
                "move_direction": "",
                "qty": line.quantity,
                "type": "account"
            })

    for move, lines in stock_moves:
        for line in lines:
            # Normalize date to datetime
            normalized_date = line.date if isinstance(line.date, datetime) else datetime.combine(line.date, datetime.min.time())
            rows.append({
                "date": normalized_date,
                "record_type": "stock_move",
                "name": move.display_name,
                "id": f"{line.move_id.id}/{line.id}",
                "price_unit": "",
                "source_location": line.location_id.display_name,
                "destination_location": line.location_dest_id.display_name,
                "move_direction": get_direction(line.location_id, line.location_dest_id),
                "qty": line.qty_done,
                "type": "stock"
            })

    # Sort rows by date
    rows = sorted(rows, key=lambda x: x["date"])

    # Initialize variables for AVCO calculation
    total_qty = get_stock(env, product)
    total_value = 0

    # Prepare table
    table = PrettyTable()
    table.field_names = ["Date", "Id", "Record-Type", "Name", "Price Unit", "Source Location", "Destination Location", "Direction", "Quantity", "AVCO Price"]
    table.align['Record-Type'] = 'l'
    table.align['Name'] = 'l'

    avco_price = 0
    for row in rows:

        if row["type"] == "account":
            # Update total value and quantity for account moves
            if isinstance(row["price_unit"], (int, float)) and row["qty"]:
                total_value += row["price_unit"] * row["qty"]
                total_qty += row["qty"]

        if row["type"] == "stock":
            # Update based on direction
            if row["move_direction"] == "incoming":
                # Add stock for incoming moves (supplier → internal or customer → internal)
                if isinstance(row["price_unit"], (int, float)) and row["qty"]:
                    total_value += row["price_unit"] * row["qty"]
                    total_qty += row["qty"]
            elif row["move_direction"] == "outgoing":
                # Remove stock for outgoing moves (internal → customer)
                total_qty -= row["qty"]
                #if total_qty < 0:
                #    raise Exception(f"Negative stock for product: {product.display_name}")
            elif row["move_direction"] == "neutral":
                # No effect on AVCO for neutral moves
                pass

        # Calculate AVCO price if there is stock
        if total_qty > 0:
            avco_price = total_value / total_qty
        else:
            avco_price = ""  # No quantity, AVCO cannot be calculated

        # Add row to the table
        table.add_row([
            row["date"].strftime('%Y-%m-%d %H:%M:%S'),
            row["id"],
            row["record_type"],
            row["name"],
            row["price_unit"] if row["price_unit"] != "" else "",
            row["source_location"],
            row["destination_location"],
            row["move_direction"],
            row["qty"],
            round(avco_price, 2) if isinstance(avco_price, (int, float)) else avco_price
        ])

    avco_rounded = round(avco_price, 3) if isinstance(avco_price, (int, float)) and avco_price != 0 else avco_price
    return {'product': product, 'table': table, 'avco_price': avco_rounded}

run(execute)
