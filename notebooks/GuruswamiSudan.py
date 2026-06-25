from sage.all import*

def G_Poly(eval,R):
    x = R.gen()
    G = 1
    for xi in eval:
        G *= (x-xi)
    return G


def LagrangePolynomials(eval, R, n):
    x = R.gen()
    L = vector(R, [1]*n)
    for i in range(n):
        for l in range(n):
            if l == i:
                continue
            L[i] *= (x-eval[l])/(eval[i]-eval[l])
    return L


def R_Poly(L,r,n):
    RX = 0
    for i in range(n):
        RX += r[i]*L[i]

    return RX


def SudanListDecoding(eval,r,l,R,k):
    n = eval.length()
    G = G_Poly(eval,R)
    L = LagrangePolynomials(eval, R, n)
    RX = R_Poly(L,r,n)
    M = matrix.identity(R, l+1, l+1)
    M[0,0] = G
    for i in range(1,l+1):
        M[i,0] = -RX**i
    W = vector(ZZ, range(l+2))
    M = WeakPopov(M,W)
    # Choose row with lowest weightet degree
    best_row = None
    best_degree = None
    for i in range(l+1):
        rowdegree = None
        for j in range(l+1):
            if rowdegree is None:
                rowdegree = M[i,j].degree()+W[j]
            else:
                rowdegree = max(M[i,j].degree()+W[j], rowdegree)
        if best_degree is None or best_degree >= rowdegree:
            best_row = i
            best_degree = rowdegree
    Q = 0
    for i in range(l+1):
        Q += M[best_row][i]*y**i
    print(Q)
    
    # Check that f agrees with enough points

    candidates = []
    valid_candidates = []
    tau = floor(n*l/(l+1)-l/2*(k-1))
    threshold = n - tau

    for factor, _ in Q.factor():
        if factor.degree(y) == 1:
            a = factor.coefficient(y) 
            b = factor - a*y 

            f = -b / a      
            candidates.append(f)

            agreements = 0
            for xi, ri in zip(eval, r):
                if f(xi,y) == ri:
                    agreements += 1
            if agreements >= threshold:
                valid_candidates.append(f)
    return candidates, valid_candidates    


def GuruswamiSudanListDecoding(eval,r,l,q,k,m=1):
    n = eval.length()

    F = GF(q)
    R = PolynomialRing(F, "x,y")

    # CHANGED: make a univariate ring S = F[x] for the Popov matrix
    F = R.base_ring()
    S = PolynomialRing(F, "x")
    xS = S.gen()

    # CHANGED: keep bivariate variables only for final Q and factorization
    x, y = R.gens()

    # CHANGED: compute G and RX in S, not in R = F[x,y]
    G = prod(xS - S(xi) for xi in eval)
    L = LagrangePolynomials(eval, S, n)
    RX = R_Poly(L, r, n)

    # CHANGED: build matrix over S = F[x]
    M = zero_matrix(S, l+1, l+1)

    # CHANGED: standard multiplicity basis:
    # for i <= m:  G^(m-i)(y-RX)^i
    # for i >  m:  y^(i-m)(y-RX)^m
    for i in range(l+1):
        if i <= m:
            for j in range(i+1):
                M[i,j] = binomial(i,j) * (-RX)**(i-j) * G**(m-i)
        else:
            for j in range(m+1):
                M[i,j+i-m] = binomial(m,j) * (-RX)**(m-j)

    # CHANGED: weighted degree should be x-degree + j*(k-1)
    W = vector(ZZ, [j*(k-1) for j in range(l+1)])

    M = WeakPopov(M,W) #Can use weakpopov and popov

    # Choose row with lowest weighted degree
    best_row = None
    best_degree = None
    for i in range(l+1):
        rowdegree = None
        for j in range(l+1):
            if M[i,j] == 0:       # CHANGED: skip zero entries
                continue

            deg = M[i,j].degree() + W[j]

            if rowdegree is None:
                rowdegree = deg
            else:
                rowdegree = max(deg, rowdegree)

        if rowdegree is not None and (best_degree is None or best_degree >= rowdegree):
            best_row = i
            best_degree = rowdegree

    # CHANGED: reconstruct Q in the bivariate ring R
    Q = 0
    for i in range(l+1):
        Q += R(M[best_row][i]) * y**i

    print(Q)

    candidates = []
    valid_candidates = []

    # CHANGED: multiplicity decoding condition
    threshold = floor(best_degree/m) + 1

    for factor, _ in Q.factor():
        if factor.degree(y) == 1:
            a = factor.coefficient(y)
            b = factor - a*y

            f = -b / a
            candidates.append(f)

            agreements = 0
            for xi, ri in zip(eval, r):
                if f(xi, y) == ri:
                    agreements += 1

            if agreements >= threshold:
                valid_candidates.append(f)

    return candidates, valid_candidates