from sage.all import*


def Pivot(A, i, W):
    m = A.ncols()
    I = -1
    D = -1
    DW = -1  # shifted pivot degree

    for j in range(m):
        if A[i,j] != 0:
            if A[i,j].degree() + W[j] >= DW: 
                DW = A[i,j].degree()+W[j]
                D = A[i,j].degree()
                I = j

    return (I, D, DW)


def SimpleTransformation(A,i,j,I,d_i,d_j):
    m = A.ncols()
    d = d_i-d_j

    cxe = (A[i,I].leading_coefficient() / A[j,I].leading_coefficient())*(x**d)
    for l in range(m):
        A[i,l] = A[i,l] - cxe*A[j,l]

    return A


def WeakPopov(A,W=0):
    n = A.nrows()
    # If no weights are given, set W = [0,0,...,0]
    if W == 0:
        W=zero_vector(ZZ, A.nrows())
        
    pivots = zero_matrix(ZZ, n, 2)

    control = 1

    for i in range(n):
        pivots[i,0] = Pivot(A,i,W)[0] 
        pivots[i,1] = Pivot(A,i,W)[1]

    while control == 1:

        control = 0
        broke = False

        for i in range(n):
            for j in range(i+1,n):
                if pivots[i,0] != -1 and pivots[j,0] != -1 and pivots[i,0] == pivots[j,0]:
                    if pivots[i,1] >= pivots[j,1]:
                        A = SimpleTransformation(A,i,j,pivots[i,0],pivots[i,1],pivots[j,1])
                        pivots[i,0] = Pivot(A,i,W)[0]
                        pivots[i,1] = Pivot(A,i,W)[1]
                    else:
                        A = SimpleTransformation(A,j,i,pivots[j,0],pivots[j,1],pivots[i,1])
                        pivots[j,0] = Pivot(A,j,W)[0]
                        pivots[j,1] = Pivot(A,j,W)[1]
                    control = 1
                    broke = True
                    break
            if broke:
                break
                        
    return A