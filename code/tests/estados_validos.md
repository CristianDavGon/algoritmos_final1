# Estados iniciales válidos por red

Un estado es **válido** si puede ser alcanzado como destino de alguna transición en la TPM
(PyPhi lanza error si el estado inicial no es alcanzable).

La tabla fue generada automáticamente leyendo cada TPM y calculando el conjunto imagen
de la función de transición `next_state = argmax(tpm[i])` para cada estado `i`.

---

## N5A — 5 nodos, página A

**8 de 32 estados son alcanzables.**

| Binario   | # unos | Usar en `ESTADO_INICIO` |
|-----------|--------|--------------------------|
| `00000`   | 0      | `"00000"`                |
| `00100`   | 1      | `"00100"`                |
| `10000`   | 1      | `"10000"`                |
| `10001`   | 2      | `"10001"`                |
| `10100`   | 2      | `"10100"`                |
| `10101`   | 3      | `"10101"`                |
| `11001`   | 3      | `"11001"`                |
| `11100`   | 3      | `"11100"`                |

> **Nota:** `11111` (todos unos) **no es alcanzable** en esta red.

---

## N5B — 5 nodos, página B

**13 de 32 estados son alcanzables.**

| Binario   | # unos | Usar en `ESTADO_INICIO` |
|-----------|--------|--------------------------|
| `00000`   | 0      | `"00000"`                |
| `00010`   | 1      | `"00010"`                |
| `00100`   | 1      | `"00100"`                |
| `00110`   | 2      | `"00110"`                |
| `00111`   | 3      | `"00111"`                |
| `01010`   | 2      | `"01010"`                |
| `01100`   | 2      | `"01100"`                |
| `01110`   | 3      | `"01110"`                |
| `01111`   | 4      | `"01111"`                |
| `10110`   | 3      | `"10110"`                |
| `10111`   | 4      | `"10111"`                |
| `11010`   | 3      | `"11010"`                |
| `11110`   | 4      | `"11110"`                |

> **Nota:** `11111` (todos unos) **no es alcanzable** en esta red.  
> Con 4 unos las opciones válidas son: `01111`, `10111`, `11110`.

---

## N8A — 8 nodos, página A

**Los 256 de 256 estados son alcanzables** — cualquier combinación binaria de 8 bits es válida.

Se listan representantes por cantidad de unos para referencia rápida:

| # unos | Ejemplos                              |
|--------|---------------------------------------|
| 0      | `00000000`                            |
| 1      | `10000000`, `00000001`                |
| 2      | `11000000`, `10000001`, `00000011`    |
| 3      | `11100000`, `10100001`, `00000111`    |
| 4      | `11110000`, `10101010`, `00001111`    |
| 5      | `11111000`, `10101011`, `00011111`    |
| 6      | `11111100`, `10110111`, `00111111`    |
| 7      | `11111110`, `01111111`                |
| 8      | `11111111`                            |

> Cualquier string de 8 caracteres `0`/`1` es válido para esta red.

---

## N10A — 10 nodos, página A

**645 de 1024 estados son alcanzables.**

Se muestran representantes seleccionados por cantidad de unos.
Para la lista completa, ejecutar el script de validación (ver abajo).

| # unos | Ejemplos de estados válidos                             |
|--------|---------------------------------------------------------|
| 0      | `0000000000`                                            |
| 1      | `0000000001`, `0000000100`, `0000010000`, `1000000000`  |
| 2      | `0000000101`, `0000000110`, `0000001100`, `1000000000`* |
| 3      | `0000000111`, `0000001011`, `0000001101`, `1010000001`  |
| 4      | `0000001111`, `0000010111`, `0000110101`, `1010000101`  |
| 5      | `0000110111`, `0001111001`, `1010101101`, `1111000001`  |
| 6      | `0001110111`, `0110111111`, `1010111101`, `1111000011`  |
| 7      | `0101110111`, `0111011011`, `1011011111`, `1110011111`  |
| 8      | `0110111111`, `0111101111`, `1010111111`, `1110110111`  |
| 9      | `0111111111`, `1001111111`, `1111011111`, `1111110111`  |
| 10     | *(ninguno — `1111111111` no es alcanzable)*             |

> **Nota:** `1111111111` (todos unos) **no es alcanzable** en N10A.


---

## Resumen de cobertura

| Red   | Alcanzables | Total | Cobertura |
|-------|-------------|-------|-----------|
| N5A   | 8           | 32    | 25 %      |
| N5B   | 13          | 32    | 41 %      |
| N8A   | 256         | 256   | 100 %     |
| N10A  | 645         | 1024  | 63 %      |
