def MakeMonic(A,pivots,n,m):

    for i in range(n):
        if A[i,pivots[i,0]].leading_coefficient() != 1 and A[i,pivots[i,0]].leading_coefficient() != 0:
            monic_const = 1 / A[i,pivots[i,0]].leading_coefficient() 
            for j in range(m):
                A[i,j] = monic_const*A[i,j]  
    return A   


def AscendingOrder(A, W):
    n = A.nrows()
    check = 1
    while check == 1:
        check = 0
        for i in range(n-1):
            I1, D1, DW1 = Pivot(A, i, W)
            I2, D2, DW2 = Pivot(A, i+1, W)

            if DW1 > DW2:
                A.swap_rows(i, i+1)
                check = 1
            elif DW1 == DW2:
                if I1 > I2:
                    A.swap_rows(i, i+1)
                    check = 1
    return A


def PopovForm(A,W=0):
    n = A.nrows()
    # If no weights are given, set W = [0,0,...,0]
    if W == 0:
        W = zero_vector(ZZ, A.ncols())
    m = A.ncols()
    pivots = zero_matrix(ZZ, n, 2)
    C = []

    A = WeakPopov(A,W)
    A = AscendingOrder(A,W)

    for i in range(n):
        pivots[i,0] = Pivot(A,i,W)[0]
        pivots[i,1] = Pivot(A,i,W)[1]
    
    for k in range(n):
        if not A[k].is_zero():
            C.append(k)
            for i in C:
                if i<k:
                    delta = A[k,pivots[i,0]].degree() - pivots[i,1]
                    if delta >= 0:
                        A = SimpleTransformation(A,k,i,pivots[i,0],A[k,pivots[i,0]].degree(),pivots[i,1])
    A = MakeMonic(A,pivots,n,m)  
      
    return A