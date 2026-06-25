from sage.all import GF, PolynomialRing, Matrix, Infinity

NEG_INF = -Infinity  # Sage has Infinity/-Infinity

def _deg_poly(p):
    return p.degree() if p != 0 else NEG_INF

def row_degree(row):
    return max(_deg_poly(e) for e in row)

def leading_position(row):
    d = row_degree(row)
    if d == NEG_INF:
        return None
    lp = None
    for j, e in enumerate(row):
        if _deg_poly(e) == d:
            lp = j
    return lp

def is_weak_popov(M):
    lps = []
    for i in range(M.nrows()):
        lp = leading_position(M.row(i))
        if lp is not None:
            lps.append(lp)
    return len(lps) == len(set(lps))

def simple_transformation_first_kind(M, i, j):
    ri = M.row(i)
    rj = M.row(j)

    lpi = leading_position(ri)
    lpj = leading_position(rj)
    if lpi is None or lpj is None or lpi != lpj:
        return False

    di = row_degree(ri)
    dj = row_degree(rj)

    if di < dj:
        i, j = j, i
        ri, rj = rj, ri
        di, dj = dj, di
        lpi = lpj

    lp = lpi
    a = ri[lp]
    b = rj[lp]
    if a == 0 or b == 0:
        return False

    shift = di - dj
    R = a.parent()
    x = R.gen()
    factor = (a.leading_coefficient() / b.leading_coefficient()) * (x**shift)

    M.set_row(i, ri - factor * rj)
    return True

def WeakPopovForm(M):
    # FIX: polynomial matrices may not have .copy()
    A = Matrix(M)   # makes a fresh matrix with same entries

    while not is_weak_popov(A):
        reduced = False

        lp_to_rows = {}
        for i in range(A.nrows()):
            lp = leading_position(A.row(i))
            if lp is None:
                continue
            lp_to_rows.setdefault(lp, []).append(i)

        for lp, rows in lp_to_rows.items():
            if len(rows) >= 2:
                i, j = rows[0], rows[1]
                if simple_transformation_first_kind(A, i, j):
                    reduced = True
                    break

        if not reduced:
            raise RuntimeError("No reducible pair found, but matrix is not in weak Popov form.")

    return A

# -------------------------
# Example
# -------------------------
if __name__ == "__main__":
    F = GF(7)
    R = PolynomialRing(F, "x")
    x = R.gen()

    M = Matrix(R, [
        [x**3 + 2*x,      x**2 + 1,    3*x],
        [2*x**3 + x**2,   4*x**2,      x + 6],
        [0,               x**3,        2*x**2 + 5],
    ])

    N = WeakPopovForm(M)
    print("Original M:\n", M)
    print("\nWeak Popov form N:\n", N)
    print("\nIs weak Popov?", is_weak_popov(N))

