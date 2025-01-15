from flask import Flask, request, jsonify, render_template
from mendeleev import element
import re

app = Flask(__name__)

# Function to fetch atomic weight using mendeleev
def fetch_atomic_weight(element_symbol):
    try:
        el = element(element_symbol)  # Fetch element object
        return el.atomic_weight       # Return atomic weight
    except KeyError:
        raise ValueError(f"Element '{element_symbol}' is not recognized or not part of the periodic table.")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while fetching data for element '{element_symbol}': {e}")

# Parse chemical formula, including nested parentheses and hydrates
def parse_formula(formula):
    def parse_group(formula):
        stack = []
        i = 0

        while i < len(formula):
            char = formula[i]

            if char == '(':
                # Handle nested parentheses
                open_parens = 1
                j = i + 1
                while j < len(formula) and open_parens > 0:
                    if formula[j] == '(':
                        open_parens += 1
                    elif formula[j] == ')':
                        open_parens -= 1
                    j += 1

                if open_parens != 0:
                    raise ValueError("Unmatched parentheses in formula.")

                # Parse the inner group
                inner_group = parse_group(formula[i + 1:j - 1])

                # Find the multiplier after the parentheses
                k = j
                while k < len(formula) and formula[k].isdigit():
                    k += 1

                multiplier = int(formula[j:k]) if k > j else 1

                # Multiply counts in the inner group
                for elem, count in inner_group:
                    stack.append((elem, count * multiplier))

                i = k - 1

            elif char.isalpha():
                # Parse element symbols
                j = i + 1
                while j < len(formula) and formula[j].islower():
                    j += 1

                # Check for count after the element
                k = j
                while k < len(formula) and formula[k].isdigit():
                    k += 1

                element_symbol = formula[i:j]
                count = int(formula[j:k]) if k > j else 1
                stack.append((element_symbol, count))

                i = k - 1

            else:
                raise ValueError(f"Unexpected character '{char}' in formula. Only valid characters are letters, numbers, parentheses, and '.' or '·' for hydrates.")

            i += 1

        return stack

    if not formula or not isinstance(formula, str):
        raise ValueError("Invalid formula: Formula must be a non-empty string.")

    # Handle hydrate symbols '.' and '·'
    if '.' in formula:
        parts = formula.split('.')
        if len(parts) != 2:
            raise ValueError("Invalid hydrate format. Only one '.' is allowed in the formula.")
        main_formula, hydrate = parts

        # Validate and parse the hydrate format
        hydrate = hydrate.strip()
        hydrate_match = re.match(r"^(\d*)(H2O)$", hydrate)
        if not hydrate_match:
            raise ValueError("Invalid hydrate format after '.'. Must be in the form 'nH2O' or 'H2O'.")

        # Extract the multiplier and hydrate group
        multiplier = int(hydrate_match.group(1)) if hydrate_match.group(1) else 1
        hydrate_group = hydrate_match.group(2)

        parsed_main = parse_group(main_formula.strip())
        parsed_hydrate = parse_group(hydrate_group.strip())

        # Multiply counts in the hydrate group
        parsed_hydrate = [(elem, count * multiplier) for elem, count in parsed_hydrate]

        # Combine results
        combined = parsed_main + parsed_hydrate
    elif "·" in formula:
        parts = formula.split("·")
        if len(parts) != 2:
            raise ValueError("Invalid hydrate format. Only one '·' is allowed in the formula.")
        main_formula, hydrate = parts

        # Parse main formula and hydrate
        parsed_main = parse_group(main_formula.strip())
        parsed_hydrate = parse_group(hydrate.strip())

        combined = parsed_main + parsed_hydrate
    else:
        # Parse single formula
        combined = parse_group(formula.strip())

    # Flatten and combine counts
    parsed = {}
    for elem, count in combined:
        parsed[elem] = parsed.get(elem, 0) + count

    return list(parsed.items())


# Calculate molecular weight
def calculate_molecular_weight(formula):
    try:
        parsed_formula = parse_formula(formula)
        molecular_weight = 0
        for element_symbol, count in parsed_formula:
            weight = fetch_atomic_weight(element_symbol)
            if weight:
                molecular_weight += weight * count
            else:
                raise ValueError(f"Atomic weight not found for element '{element_symbol}'")
        return molecular_weight
    except Exception as e:
        raise ValueError(f"Error calculating molecular weight: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()

    # Validate input data
    if not data or 'formula' not in data:
        return jsonify({'error': 'No formula provided. Please provide a valid chemical formula.'}), 400

    formula = data.get('formula')

    if not formula or not isinstance(formula, str):
        return jsonify({'error': 'Invalid formula. It must be a non-empty string.'}), 400

    try:
        weight = calculate_molecular_weight(formula)
        return jsonify({'molecular_weight': weight})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
