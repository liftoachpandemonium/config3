import re
import argparse
import toml

class ConfigParser:
    def __init__(self, input_text):
        self.text = input_text
        self.variables = {}

    def parse(self):
        """Основной метод обработки текста."""
        self.text = self._remove_multiline_comments(self.text)
        lines = self.text.splitlines()
        output = {}
        constant_expressions = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if '->' in line:
                self._parse_constant_declaration(line)
            elif line.startswith('^{') and line.endswith('}'):
                constant_expressions.append(line)
            else:
                key, value = self._parse_key_value(line)
                output[key] = value

        # Добавление выражений
        for line in constant_expressions:
            result = self._evaluate_constant_expression(line)
            output.update(result)

        # Только значения выражений
        output = {key: value for key, value in output.items() if not isinstance(value, list)}
        
        return output

    def _remove_multiline_comments(self, text):
        """Удаление многострочных комментариев."""
        return re.sub(r'{-.*?-}', '', text, flags=re.DOTALL)

    def _parse_constant_declaration(self, line):
        """Обработка объявления константы."""
        value, name = map(str.strip, line.split('->'))
        self.variables[name] = self._parse_value(value)

    def _evaluate_constant_expression(self, line):
        """Обработка вычисления выражений в формате ^{...}"""
        expression = line[2:-1].strip()
        try:
            result = eval(expression, {**self.variables, 'sort': sorted, 'ord': ord})
            return {expression: result}
        except Exception as e:
            raise ValueError(f"Ошибка вычисления выражения {expression}: {e}")

    def _parse_key_value(self, line):
        """Обработка строки вида ключ = значение."""
        if '=' not in line:
            raise ValueError(f"Некорректная строка: {line}")

        key, value = map(str.strip, line.split('=', 1))
        if not re.match(r'^[_\w][_\w\d]*$', key):
            raise ValueError(f"Недопустимое имя ключа: {key}")

        parsed_value = self._parse_value(value)
        self.variables[key] = parsed_value  # Сохраняем переменную
        return key, parsed_value

    def _parse_value(self, value):
        """Разбор значения (число, строка или массив)."""
        if value.isdigit():
            return int(value)
        elif value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith('list(') and value.endswith(')'):
            items = value[5:-1].split(',')
            return [self._parse_value(item.strip()) for item in items]
        elif value in self.variables:
            return self.variables[value]
        else:
            raise ValueError(f"Неизвестное значение: {value}")

# Относительно тестов
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Транслятор учебного конфигурационного языка в TOML.")
    parser.add_argument("-i", "--input", required=True, help="Путь к входному файлу конфигурации.")
    parser.add_argument("-o", "--output", required=True, help="Путь к выходному файлу TOML.")
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as file:
        input_text = file.read()

    config_parser = ConfigParser(input_text)
    try:
        result = config_parser.parse()
    except ValueError as e:
        print(f"Ошибка: {e}")
        exit(1)

    with open(args.output, 'w', encoding='utf-8') as toml_file:
        toml.dump(result, toml_file)

    print(f"Конфигурация сохранена в {args.output}")
