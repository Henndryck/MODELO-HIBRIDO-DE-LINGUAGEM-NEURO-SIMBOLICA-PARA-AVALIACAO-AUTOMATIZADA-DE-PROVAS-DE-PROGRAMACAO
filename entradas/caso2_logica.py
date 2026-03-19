def ordenar_vetor(lista):
    n = len(lista)
    for i in range(n):
        for j in range(0, n):
            if lista[j] > lista[j + 1]:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]
    return lista



