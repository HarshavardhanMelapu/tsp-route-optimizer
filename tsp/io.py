import csv
import io
import math
from pathlib import Path

from tsp.models import City, TspInstance


_X_COLUMNS = {"x", "longitude", "lon", "coord_x"}
_Y_COLUMNS = {"y", "latitude", "lat", "coord_y"}
_ID_COLUMNS = {"id", "city", "name", "node"}


def _validate_cities(cities: list[City], name: str) -> tuple[City, ...]:
    if len(cities) < 2:
        raise ValueError("The dataset must contain at least two cities.")

    identifiers = [city.identifier for city in cities]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("City identifiers must be unique.")

    return tuple(cities)


def parse_tsplib(text: str, name: str = "uploaded instance") -> TspInstance:
    headers: dict[str, str] = {}
    coordinate_lines: list[str] = []
    in_coordinates = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if in_coordinates:
            if line.upper() == "EOF":
                break
            coordinate_lines.append(line)
            continue
        if line.upper() == "NODE_COORD_SECTION":
            in_coordinates = True
            continue

        if ":" in line:
            key, value = line.split(":", 1)
        else:
            fields = line.split(maxsplit=1)
            if len(fields) != 2:
                continue
            key, value = fields
        headers[key.strip().upper()] = value.strip()

    if not in_coordinates:
        raise ValueError("TSPLIB input is missing NODE_COORD_SECTION.")
    if headers.get("EDGE_WEIGHT_TYPE", "").upper() != "EUC_2D":
        raise ValueError("Only TSPLIB EDGE_WEIGHT_TYPE EUC_2D is supported.")

    try:
        expected_dimension = int(headers["DIMENSION"])
    except (KeyError, ValueError) as error:
        raise ValueError("TSPLIB input must declare a valid DIMENSION.") from error

    cities: list[City] = []
    for line in coordinate_lines:
        fields = line.split()
        if len(fields) != 3:
            raise ValueError(f"Invalid TSPLIB coordinate row: {line!r}")
        try:
            x, y = float(fields[1]), float(fields[2])
        except ValueError as error:
            raise ValueError(f"Invalid coordinates in TSPLIB row: {line!r}") from error
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError(f"Coordinates must be finite in TSPLIB row: {line!r}")
        cities.append(City(fields[0], x, y))

    if len(cities) != expected_dimension:
        raise ValueError(
            f"TSPLIB DIMENSION is {expected_dimension}, but "
            f"{len(cities)} coordinate rows were found."
        )

    instance_name = headers.get("NAME", name)
    return TspInstance(
        name=instance_name,
        cities=_validate_cities(cities, instance_name),
        round_distances=True,
        source_format="TSPLIB EUC_2D",
    )


def parse_csv(text: str, name: str = "uploaded CSV") -> TspInstance:
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    rows = [
        [value.strip() for value in row]
        for row in csv.reader(io.StringIO(text), dialect)
        if any(value.strip() for value in row)
    ]
    if not rows:
        raise ValueError("The CSV file is empty.")

    headings = [value.lower() for value in rows[0]]
    x_index = next((i for i, heading in enumerate(headings) if heading in _X_COLUMNS), None)
    y_index = next((i for i, heading in enumerate(headings) if heading in _Y_COLUMNS), None)
    has_header = x_index is not None and y_index is not None

    if has_header:
        id_index = next(
            (i for i, heading in enumerate(headings) if heading in _ID_COLUMNS),
            None,
        )
        data_rows = rows[1:]
    else:
        if len(rows[0]) == 2:
            id_index, x_index, y_index = None, 0, 1
        elif len(rows[0]) == 3:
            id_index, x_index, y_index = 0, 1, 2
        else:
            raise ValueError(
                "CSV needs x and y columns, or two coordinate columns "
                "(optionally preceded by an ID)."
            )
        data_rows = rows

    cities: list[City] = []
    for row_number, row in enumerate(data_rows, start=2 if has_header else 1):
        if max(x_index, y_index) >= len(row):
            raise ValueError(f"CSV row {row_number} is missing a coordinate.")
        identifier = row[id_index] if id_index is not None and id_index < len(row) else str(
            len(cities) + 1
        )
        try:
            x, y = float(row[x_index]), float(row[y_index])
        except ValueError as error:
            raise ValueError(f"CSV row {row_number} has a non-numeric coordinate.") from error
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError(f"CSV row {row_number} coordinates must be finite.")
        cities.append(City(identifier, x, y))

    return TspInstance(
        name=Path(name).stem or "uploaded CSV",
        cities=_validate_cities(cities, name),
        round_distances=False,
        source_format="CSV",
    )


def parse_instance(filename: str, text: str) -> TspInstance:
    if Path(filename).suffix.lower() in {".tsp", ".tsplib"} or (
        "NODE_COORD_SECTION" in text.upper()
    ):
        return parse_tsplib(text, Path(filename).stem)
    return parse_csv(text, Path(filename).stem)
