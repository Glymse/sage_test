from sage.all import*


def is_reduced(A,W=0):
    n, m = A.nrows(), A.ncols()

    # If no weights are given, set W = [0,0,...,0]
    if W == 0:
        W=zero_vector(ZZ, A.nrows())
        
    piv = [Pivot(A,i,W) for i in range(n)]  # (I)

    # gather nonzero rows
    nz = [i for i in range(n) if not A[i].is_zero()]

    # distinct pivot columns among nonzero rows
    cols = [piv[i][0] for i in nz]
    if len(set(cols)) != len(cols):
        return False

    return True


def WeightedDegreeOfMatrix(A,W):
    n = A.nrows()
    m=A.ncols()
    max_deg = -oo

    for i in range(n):
        for j in range(m):
            max_deg = max(A[i,j].degree()+W[j], max_deg)
    return max_deg


def LastRecursion(A,R,W=0):
    # If no weights are given, set W = [0,0,...,0]
    if W == 0:
        W=zero_vector(ZZ, A.ncols())
        
    D_old = WeightedDegreeOfMatrix(A,W)
    D_new = oo
    n = A.nrows()
    U = matrix.identity(R, n, n)
    
    
    pivots = zero_matrix(ZZ, n, 2)

    for i in range(n):
        pivots[i,0] = Pivot(A,i,W)[0] 
        pivots[i,1] = Pivot(A,i,W)[1]

    while D_old <= D_new:

        if is_reduced(A):
            return U

        broke = False

        for i in range(n):
            for j in range(i+1,n):
                if pivots[i,0] == pivots[j,0]:
                    if pivots[i,1] >= pivots[j,1]:
                        D_old = A.row_degrees()[i]
                        A, U = SimpleTransformation(A,U,i,j,pivots[i,0],pivots[i,1],pivots[j,1])
                        D_new = A.row_degrees()[i]
                        pivots[i,0] = Pivot(A,i,W)[0]
                        pivots[i,1] = Pivot(A,i,W)[1]
                    else:
                        D_old = A.row_degrees()[j]
                        A, U = SimpleTransformation(A,U,j,i,pivots[j,0],pivots[j,1],pivots[i,1])
                        D_new = A.row_degrees()[j]
                        pivots[j,0] = Pivot(A,j,W)[0]
                        pivots[j,1] = Pivot(A,j,W)[1]
                    broke = True
                    break
            if broke:
                break
                        
    return U


def AccuracyApproximation(A,t,W=0):
    # If no weights are given, set W = [0,0,...,0]
    if W == 0:
        W=zero_vector(ZZ, A.nrows())

    m = A.ncols()
    n = A.nrows()
    A_approx = zero_matrix(R, n, m)
    A_copy = copy(A)

    # Calculate the maximum degree for each row
    row_degrees = [max(entry.degree() for entry in row) for row in A.rows()]

    for i in range(n):
        for j in range(m):
            LT = A_copy[i,j].lt() # Leading term
            while (LT.degree()+W[j] > row_degrees[i]-t) and (A_copy[i,j] != 0):
                A_approx[i,j] += LT
                A_copy[i,j] -= LT
                LT = A_copy[i,j].lt() # Leading term
    return A_approx


def Alekhnovich(A,R,t, W=0):
    # If no weights are given, set W = [0,0,...,0]
    if W == 0:
        W=zero_vector(ZZ, A.ncols())

    A_approx = AccuracyApproximation(A,t)

    # Extra termination check:
    # If A is already reduced, the identity matrix is a valid U_w(A,t).
    if is_reduced(A_approx):
        return identity_matrix(R, A.nrows())
    
    if t==1:
        #A_placeholder = copy(A_approx)
        #print(LastRecursion(A_placeholder,R))
        return LastRecursion(A_approx,R)
    else:
        U_prime = Alekhnovich(A_approx,R,floor(t/2))
        A_prime = U_prime*A_approx
        # Important termination check:
        # If the first recursive call already reduced the matrix, stop.
        if is_reduced(A_prime):
            return U_prime
        return Alekhnovich(A_prime,R,t-(WeightedDegreeOfMatrix(A_approx,W)-WeightedDegreeOfMatrix(A_prime,W)))*U_prime