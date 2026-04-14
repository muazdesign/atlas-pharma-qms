"""
Atlas Pharma QMS — AQL Sampling Engine
Implements ANSI/ASQ Z1.4 (attributes) and Z1.9 (variables) sampling plans
based on ISO 2859-1 standard.

Usage:
    from data.aql_tables import get_aql_sample_size, get_code_letter

References:
    - ANSI/ASQ Z1.4-2003 (Sampling Procedures and Tables for Inspection
      by Attributes)
    - ANSI/ASQ Z1.9-2003 (Sampling Procedures and Tables for Inspection
      by Variables)
    - ISO 2859-1:1999
"""


# ---------------------------------------------------------------------------
# Table 1 — Sample Size Code Letters
# Maps (batch_size_range, inspection_level) → code letter
# Inspection levels: S-1, S-2, S-3, S-4 (special), I, II (normal), III
# ---------------------------------------------------------------------------

# Batch size ranges as (min, max) tuples
_BATCH_RANGES = [
    (2, 8),
    (9, 15),
    (16, 25),
    (26, 50),
    (51, 90),
    (91, 150),
    (151, 280),
    (281, 500),
    (501, 1200),
    (1201, 3200),
    (3201, 10000),
    (10001, 35000),
    (35001, 150000),
    (150001, 500000),
    (500001, float('inf')),
]

# Code letter table: each row matches _BATCH_RANGES index
# Columns: S-1, S-2, S-3, S-4, I, II, III
_CODE_LETTER_TABLE = [
    # 2-8
    ['A', 'A', 'A', 'A', 'A', 'A', 'B'],
    # 9-15
    ['A', 'A', 'A', 'A', 'A', 'B', 'C'],
    # 16-25
    ['A', 'A', 'B', 'B', 'B', 'C', 'D'],
    # 26-50
    ['A', 'B', 'B', 'C', 'C', 'D', 'E'],
    # 51-90
    ['B', 'B', 'C', 'C', 'C', 'E', 'F'],
    # 91-150
    ['B', 'B', 'C', 'D', 'D', 'F', 'G'],
    # 151-280
    ['B', 'C', 'D', 'E', 'E', 'G', 'H'],
    # 281-500
    ['B', 'C', 'D', 'E', 'F', 'H', 'J'],
    # 501-1200
    ['C', 'C', 'E', 'F', 'G', 'J', 'K'],
    # 1201-3200
    ['C', 'D', 'E', 'G', 'H', 'K', 'L'],
    # 3201-10000
    ['C', 'D', 'F', 'G', 'J', 'L', 'M'],
    # 10001-35000
    ['D', 'E', 'G', 'H', 'K', 'M', 'N'],
    # 35001-150000
    ['D', 'E', 'G', 'J', 'L', 'N', 'P'],
    # 150001-500000
    ['D', 'E', 'H', 'K', 'M', 'P', 'Q'],
    # 500001+
    ['D', 'E', 'H', 'K', 'N', 'Q', 'R'],
]

_LEVEL_INDEX = {
    'S-1': 0, 'S-2': 1, 'S-3': 2, 'S-4': 3,
    'I': 4, 'II': 5, 'III': 6,
}


# ---------------------------------------------------------------------------
# Table 2-A — Single Sampling Plans for Normal Inspection (Attributes)
# Maps code letter → sample size
# Then (code_letter, AQL) → (accept, reject)
# ---------------------------------------------------------------------------

_CODE_TO_SAMPLE_SIZE = {
    'A': 2,    'B': 3,    'C': 5,    'D': 8,
    'E': 13,   'F': 20,   'G': 32,   'H': 50,
    'J': 80,   'K': 125,  'L': 200,  'M': 315,
    'N': 500,  'P': 800,  'Q': 1250, 'R': 2000,
}

# AQL values supported (percent defective)
_AQL_VALUES = [0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.0, 1.5, 2.5, 4.0, 6.5, 10.0]

# Accept/Reject numbers for Normal Inspection (Single Sampling)
# Format: _ACCEPT_REJECT[code_letter][aql_value] = (Ac, Re)
# None means "use next higher/lower plan" (arrow rule)
_ACCEPT_REJECT = {
    'A': {
        0.065: None, 0.10: None, 0.15: None, 0.25: None,
        0.40: None, 0.65: None, 1.0: None, 1.5: None,
        2.5: None, 4.0: None, 6.5: (0, 1), 10.0: (0, 1),
    },
    'B': {
        0.065: None, 0.10: None, 0.15: None, 0.25: None,
        0.40: None, 0.65: None, 1.0: None, 1.5: None,
        2.5: None, 4.0: (0, 1), 6.5: (0, 1), 10.0: (1, 2),
    },
    'C': {
        0.065: None, 0.10: None, 0.15: None, 0.25: None,
        0.40: None, 0.65: None, 1.0: None, 1.5: None,
        2.5: (0, 1), 4.0: (0, 1), 6.5: (1, 2), 10.0: (2, 3),
    },
    'D': {
        0.065: None, 0.10: None, 0.15: None, 0.25: None,
        0.40: None, 0.65: None, 1.0: None, 1.5: (0, 1),
        2.5: (0, 1), 4.0: (1, 2), 6.5: (2, 3), 10.0: (3, 4),
    },
    'E': {
        0.065: None, 0.10: None, 0.15: None, 0.25: None,
        0.40: None, 0.65: (0, 1), 1.0: (0, 1), 1.5: (1, 2),
        2.5: (1, 2), 4.0: (2, 3), 6.5: (3, 4), 10.0: (5, 6),
    },
    'F': {
        0.065: None, 0.10: None, 0.15: None, 0.25: None,
        0.40: (0, 1), 0.65: (0, 1), 1.0: (1, 2), 1.5: (1, 2),
        2.5: (2, 3), 4.0: (3, 4), 6.5: (5, 6), 10.0: (7, 8),
    },
    'G': {
        0.065: None, 0.10: None, 0.15: None, 0.25: (0, 1),
        0.40: (0, 1), 0.65: (1, 2), 1.0: (1, 2), 1.5: (2, 3),
        2.5: (3, 4), 4.0: (5, 6), 6.5: (7, 8), 10.0: (10, 11),
    },
    'H': {
        0.065: None, 0.10: None, 0.15: (0, 1), 0.25: (0, 1),
        0.40: (1, 2), 0.65: (1, 2), 1.0: (2, 3), 1.5: (3, 4),
        2.5: (5, 6), 4.0: (7, 8), 6.5: (10, 11), 10.0: (14, 15),
    },
    'J': {
        0.065: None, 0.10: (0, 1), 0.15: (0, 1), 0.25: (1, 2),
        0.40: (1, 2), 0.65: (2, 3), 1.0: (3, 4), 1.5: (5, 6),
        2.5: (7, 8), 4.0: (10, 11), 6.5: (14, 15), 10.0: (21, 22),
    },
    'K': {
        0.065: (0, 1), 0.10: (0, 1), 0.15: (1, 2), 0.25: (1, 2),
        0.40: (2, 3), 0.65: (3, 4), 1.0: (5, 6), 1.5: (7, 8),
        2.5: (10, 11), 4.0: (14, 15), 6.5: (21, 22), 10.0: None,
    },
    'L': {
        0.065: (0, 1), 0.10: (1, 2), 0.15: (1, 2), 0.25: (2, 3),
        0.40: (3, 4), 0.65: (5, 6), 1.0: (7, 8), 1.5: (10, 11),
        2.5: (14, 15), 4.0: (21, 22), 6.5: None, 10.0: None,
    },
    'M': {
        0.065: (1, 2), 0.10: (1, 2), 0.15: (2, 3), 0.25: (3, 4),
        0.40: (5, 6), 0.65: (7, 8), 1.0: (10, 11), 1.5: (14, 15),
        2.5: (21, 22), 4.0: None, 6.5: None, 10.0: None,
    },
    'N': {
        0.065: (1, 2), 0.10: (2, 3), 0.15: (3, 4), 0.25: (5, 6),
        0.40: (7, 8), 0.65: (10, 11), 1.0: (14, 15), 1.5: (21, 22),
        2.5: None, 4.0: None, 6.5: None, 10.0: None,
    },
    'P': {
        0.065: (2, 3), 0.10: (3, 4), 0.15: (5, 6), 0.25: (7, 8),
        0.40: (10, 11), 0.65: (14, 15), 1.0: (21, 22), 1.5: None,
        2.5: None, 4.0: None, 6.5: None, 10.0: None,
    },
    'Q': {
        0.065: (3, 4), 0.10: (5, 6), 0.15: (7, 8), 0.25: (10, 11),
        0.40: (14, 15), 0.65: (21, 22), 1.0: None, 1.5: None,
        2.5: None, 4.0: None, 6.5: None, 10.0: None,
    },
    'R': {
        0.065: (5, 6), 0.10: (7, 8), 0.15: (10, 11), 0.25: (14, 15),
        0.40: (21, 22), 0.65: None, 1.0: None, 1.5: None,
        2.5: None, 4.0: None, 6.5: None, 10.0: None,
    },
}


# ---------------------------------------------------------------------------
# Z1.9 Variables Sampling — Sample sizes by code letter
# (Simplified table for single specification limit, normal inspection)
# ---------------------------------------------------------------------------

_VARIABLES_SAMPLE_SIZE = {
    'B': 3,   'C': 4,   'D': 5,   'E': 7,
    'F': 10,  'G': 15,  'H': 20,  'J': 25,
    'K': 35,  'L': 50,  'M': 75,  'N': 100,
    'P': 150, 'Q': 200, 'R': 300,
}

# Z1.9 "k" values (acceptability constant) for normal inspection
# Format: _VARIABLES_K[code_letter][aql] = k_value
_VARIABLES_K = {
    'B': {0.065: None, 0.10: None, 0.15: None, 0.25: None,
          0.40: None, 0.65: None, 1.0: None, 1.5: None,
          2.5: 1.237, 4.0: 0.958, 6.5: 0.566, 10.0: None},
    'C': {0.065: None, 0.10: None, 0.15: None, 0.25: None,
          0.40: None, 0.65: None, 1.0: None, 1.5: 1.450,
          2.5: 1.175, 4.0: 0.917, 6.5: 0.566, 10.0: None},
    'D': {0.065: None, 0.10: None, 0.15: None, 0.25: None,
          0.40: None, 0.65: None, 1.0: 1.653, 1.5: 1.398,
          2.5: 1.131, 4.0: 0.874, 6.5: 0.555, 10.0: None},
    'E': {0.065: None, 0.10: None, 0.15: None, 0.25: None,
          0.40: None, 0.65: 1.832, 1.0: 1.548, 1.5: 1.304,
          2.5: 1.066, 4.0: 0.828, 6.5: 0.536, 10.0: None},
    'F': {0.065: None, 0.10: None, 0.15: None, 0.25: None,
          0.40: 1.960, 0.65: 1.715, 1.0: 1.454, 1.5: 1.229,
          2.5: 1.010, 4.0: 0.790, 6.5: 0.517, 10.0: None},
    'G': {0.065: None, 0.10: None, 0.15: None, 0.25: 2.112,
          0.40: 1.876, 0.65: 1.622, 1.0: 1.382, 1.5: 1.167,
          2.5: 0.958, 4.0: 0.755, 6.5: 0.499, 10.0: None},
    'H': {0.065: None, 0.10: None, 0.15: 2.247, 0.25: 2.032,
          0.40: 1.806, 0.65: 1.555, 1.0: 1.321, 1.5: 1.118,
          2.5: 0.917, 4.0: 0.724, 6.5: 0.482, 10.0: None},
    'J': {0.065: None, 0.10: 2.335, 0.15: 2.177, 0.25: 1.971,
          0.40: 1.751, 0.65: 1.503, 1.0: 1.275, 1.5: 1.082,
          2.5: 0.886, 4.0: 0.700, 6.5: 0.469, 10.0: None},
    'K': {0.065: 2.400, 0.10: 2.275, 0.15: 2.120, 0.25: 1.917,
          0.40: 1.704, 0.65: 1.460, 1.0: 1.237, 1.5: 1.050,
          2.5: 0.859, 4.0: 0.680, 6.5: 0.455, 10.0: None},
    'L': {0.065: 2.341, 0.10: 2.220, 0.15: 2.072, 0.25: 1.874,
          0.40: 1.665, 0.65: 1.425, 1.0: 1.206, 1.5: 1.024,
          2.5: 0.837, 4.0: 0.663, 6.5: 0.444, 10.0: None},
    'M': {0.065: 2.292, 0.10: 2.176, 0.15: 2.032, 0.25: 1.839,
          0.40: 1.633, 0.65: 1.397, 1.0: 1.182, 1.5: 1.003,
          2.5: 0.819, 4.0: 0.649, 6.5: 0.435, 10.0: None},
    'N': {0.065: 2.256, 0.10: 2.143, 0.15: 2.002, 0.25: 1.811,
          0.40: 1.607, 0.65: 1.374, 1.0: 1.163, 1.5: 0.986,
          2.5: 0.805, 4.0: 0.637, 6.5: 0.427, 10.0: None},
    'P': {0.065: 2.224, 0.10: 2.113, 0.15: 1.975, 0.25: 1.786,
          0.40: 1.585, 0.65: 1.354, 1.0: 1.146, 1.5: 0.972,
          2.5: 0.793, 4.0: 0.628, 6.5: 0.421, 10.0: None},
    'Q': {0.065: 2.199, 0.10: 2.090, 0.15: 1.954, 0.25: 1.767,
          0.40: 1.567, 0.65: 1.338, 1.0: 1.133, 1.5: 0.961,
          2.5: 0.784, 4.0: 0.620, 6.5: 0.416, 10.0: None},
    'R': {0.065: 2.177, 0.10: 2.069, 0.15: 1.935, 0.25: 1.749,
          0.40: 1.551, 0.65: 1.325, 1.0: 1.122, 1.5: 0.951,
          2.5: 0.776, 4.0: 0.614, 6.5: 0.412, 10.0: None},
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_code_letter(batch_size: int, inspection_level: str = 'II') -> str:
    """Look up the sample size code letter from ANSI/ASQ Z1.4 Table 1.

    Args:
        batch_size: Lot/batch size (number of units).
        inspection_level: One of 'S-1','S-2','S-3','S-4','I','II','III'.

    Returns:
        Single uppercase code letter (A–R).

    Raises:
        ValueError: If batch_size < 2 or inspection_level is invalid.
    """
    if batch_size < 2:
        raise ValueError("Batch size must be at least 2.")

    level = inspection_level.upper().strip()
    if level not in _LEVEL_INDEX:
        raise ValueError(
            f"Invalid inspection level '{inspection_level}'. "
            f"Valid levels: {', '.join(_LEVEL_INDEX.keys())}"
        )

    col = _LEVEL_INDEX[level]

    for i, (lo, hi) in enumerate(_BATCH_RANGES):
        if lo <= batch_size <= hi:
            return _CODE_LETTER_TABLE[i][col]

    # Should not reach here, but fallback to last row
    return _CODE_LETTER_TABLE[-1][col]


def get_aql_sample_size(
    batch_size: int,
    inspection_level: str = 'II',
    aql: float = 1.0,
    sampling_type: str = 'attributes',
) -> dict:
    """Calculate the AQL sample size per ANSI/ASQ Z1.4 or Z1.9.

    Args:
        batch_size: Lot/batch size.
        inspection_level: 'S-1' through 'S-4', 'I', 'II' (normal), 'III'.
        aql: Acceptable Quality Level (percent defective).
            Supported: 0.065, 0.10, 0.15, 0.25, 0.40, 0.65,
                       1.0, 1.5, 2.5, 4.0, 6.5, 10.0
        sampling_type: 'attributes' (Z1.4) or 'variables' (Z1.9).

    Returns:
        dict with keys:
            - code_letter: str
            - sample_size: int
            - accept_number: int or None (attributes only)
            - reject_number: int or None (attributes only)
            - k_value: float or None (variables only)
            - aql: float
            - inspection_level: str
            - sampling_type: str
            - batch_size: int
            - standard: str (e.g. 'ANSI/ASQ Z1.4')
    """
    # Validate AQL
    aql_val = _nearest_aql(aql)
    code = get_code_letter(batch_size, inspection_level)

    if sampling_type.lower() == 'variables':
        return _variables_plan(batch_size, code, aql_val, inspection_level)
    else:
        return _attributes_plan(batch_size, code, aql_val, inspection_level)


def get_available_aql_values() -> list:
    """Return the list of supported AQL values."""
    return list(_AQL_VALUES)


def get_available_inspection_levels() -> list:
    """Return the list of supported inspection levels."""
    return list(_LEVEL_INDEX.keys())


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _nearest_aql(aql: float) -> float:
    """Snap to the nearest supported AQL value."""
    return min(_AQL_VALUES, key=lambda x: abs(x - aql))


def _attributes_plan(batch_size, code, aql, level):
    """Build attributes (Z1.4) sampling result."""
    sample_size = _CODE_TO_SAMPLE_SIZE[code]
    ar = _ACCEPT_REJECT.get(code, {}).get(aql)

    # Arrow rule: if None, step up to the next code letter's plan
    original_code = code
    if ar is None:
        code_letters = list(_CODE_TO_SAMPLE_SIZE.keys())
        idx = code_letters.index(code)
        # Try stepping up
        for step in range(idx + 1, len(code_letters)):
            candidate = code_letters[step]
            candidate_ar = _ACCEPT_REJECT.get(candidate, {}).get(aql)
            if candidate_ar is not None:
                ar = candidate_ar
                sample_size = _CODE_TO_SAMPLE_SIZE[candidate]
                code = candidate
                break

    accept = ar[0] if ar else 0
    reject = ar[1] if ar else 1

    return {
        'code_letter': code,
        'original_code_letter': original_code,
        'sample_size': sample_size,
        'accept_number': accept,
        'reject_number': reject,
        'k_value': None,
        'aql': aql,
        'inspection_level': level,
        'sampling_type': 'attributes',
        'batch_size': batch_size,
        'standard': 'ANSI/ASQ Z1.4 (ISO 2859-1)',
    }


def _variables_plan(batch_size, code, aql, level):
    """Build variables (Z1.9) sampling result."""
    # Z1.9 doesn't have code letter 'A', minimum is 'B'
    if code == 'A':
        code = 'B'

    sample_size = _VARIABLES_SAMPLE_SIZE.get(code, 3)
    k_val = None
    original_code = code

    k_entry = _VARIABLES_K.get(code, {}).get(aql)
    if k_entry is not None:
        k_val = k_entry
    else:
        # Arrow rule: step up
        code_letters = list(_VARIABLES_SAMPLE_SIZE.keys())
        if code in code_letters:
            idx = code_letters.index(code)
            for step in range(idx + 1, len(code_letters)):
                candidate = code_letters[step]
                candidate_k = _VARIABLES_K.get(candidate, {}).get(aql)
                if candidate_k is not None:
                    k_val = candidate_k
                    sample_size = _VARIABLES_SAMPLE_SIZE[candidate]
                    code = candidate
                    break

    return {
        'code_letter': code,
        'original_code_letter': original_code,
        'sample_size': sample_size,
        'accept_number': None,
        'reject_number': None,
        'k_value': k_val,
        'aql': aql,
        'inspection_level': level,
        'sampling_type': 'variables',
        'batch_size': batch_size,
        'standard': 'ANSI/ASQ Z1.9 (ISO 3951)',
    }
