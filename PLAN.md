# Plan: od obecnego dowodu do dowodu uznanego przez bbchallenge

Maszyna `1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD` jest na oficjalnej liście holdoutów BB(6)
(lista @mxdys, 623 maszyny, 24.10.2026, linia 124).

## Stan obecny (2026-10-26)

Dowód komputerowy jest domknięty przy założeniu poprawności symulatora symbolicznego `ssim4`
(C++): 385 węzłów, ~20 tys. lematów B, ~12 tys. lematów small-N, `verify4` 0 błędów, testy krzyżowe
z `fsim` zgodne (szczegóły w README). Do uznania brakuje formalizacji w Rocq, opisu dla ludzi
i niezależnej recenzji.

## Kroki

### 1. Zwarty opis zachowania maszyny (reguły na licznikach)
- [x] zbadać trajektorię na poziomie cykli (`an/sweepdump.c`: taśma jako lista „cyfr” przy każdym przemiataniu)
- [x] kodowanie: `Z w^N T (0 1)^M 0`, 6 wzorców strefy Z, w = `8` lub `0 3 1`, rodzina T = `0 4 3^k 2`
- [x] fazy: A (strefa zużywa P kopii w, dopisuje dM par; 3232 przemiatania na lemat A węzła startowego),
      B (konwersja `(0 1)^M` -> ~M/2 ósemek + kilka tys. par); M rośnie 8,40-8,85 razy na cykl
- [x] wniosek: dynamika strefy jest skończona i deterministyczna, ale nieregularna - nie ma zbioru kilku
      reguł licznikowych; zwarty opis = 6 stref x lematy A/B + skończona tabela przejść.
      Formalizacja musi mechanicznie sprawdzić lematy (krok 3, wariant „weryfikowany symulator”).
- [x] maszyna jest w busycoq (gałąź BB6, `verify/Eqv_Misc.v`, TM44) udowodniona jako równoważna
      `1LB0LA_1RC0LA_1RF0LD_1RA0RE_1RB---_0RD0LC` - dowód rozstrzyga obie

### 2. Opis dla ludzi (`PROOF.md`)
- [x] notacja konfiguracji, fazy A/B, schemat dowodu, skąd bierze się nieskończony wzrost
- [x] powiązanie z dowodem komputerowym (`proof4.json`, `verify4`) i baza zaufania

### 3. Formalizacja w Rocq
- [x] środowisko: Docker `coqorg/coq:8.20`, busycoq gałąź BB6 w `D:\bb_tools\busycoq` (framework zbudowany)
- [x] decydery busycoq (Inductive) na tej maszynie: domyślne ustawienia i 4 warianty (block-size 20, 10+arithseq,
      exploop, repeater-len 40) - brak decyzji (>1 h każdy, przerwane)
- [x] pilotaż: lemat A węzła startowego w Rocq (`rocq/gen_lemmaA.py` -> `rocq/lemmaA_start.v`):
      `forall n m, cfg0 n m -->+ cfg130 n (m + 1744)`, 130 pod-lematów między punktami kontrolnymi
      (co 25 przemiatań), każdy przez refleksyjny wykonawca `es'` (ES_v3); kompilacja ~2 min, bez aksjomatów.
      Lemat zachodzi dla WSZYSTKICH n, m (ograniczenia z ssim były artefaktem) -> lematy small-N / small-M zbędne.
- [ ] 3a. lemat A dla każdego węzła (205, w tym rodziny z symbolicznym k: trzecia zmienna w `es'`)
      `rocq/gen_lemmaA_all.py` -> `rocq/A/A_<tag>.v`; rodziny wymagają obrotu bloku k3 (`rocq/rot.json`, obrót 1,
      lemat dla k >= 1 kopii); sprawdzone kompilacją: węzeł startowy, węzeł `0 3 1` (27 s), pierwszy pod-lemat rodziny.
      Generowanie w toku (75/205), potem kompilacja wszystkich.
- [ ] 3b. zejście: indukcja `w^(P*j + n) -> w^n`, `M -> M + j*dM` (jeden ogólny lemat)
- [ ] 3c. reguła konwersji: wszystkie symboliczne akceleracje ssim4 mają jeden wzór (t = c + v0, jedna seria +1,
      druga -1); udowodnić ją indukcją, potem lematy B (20 122) jako es' między punktami kontrolnymi + ta reguła
- [ ] 3d. domknięcie: twierdzenie generowane z danych verify4 (przypadki (węzeł, r, parzystość), arytmetyka przez lia)
- [ ] 3e. start: `c0 -->* konfiguracja startowa` (2,26e8 kroków; zweryfikowany symulator konkretny busycoq)
- [ ] 3f. złożenie: `~ halts tm c0` przez `progress_nonhalt_cond` z niezmiennikiem „stan w dziedzinie”

### 4. Odtwarzalność
- [ ] weryfikator, który potrzebuje tylko plików z repo (bez ~20 GB śladów), albo skrypt odtwarzający wejścia
- [ ] instrukcja uruchomienia wszystkich kontroli od zera

### 5. Zgłoszenie (decyzje i działania użytkownika)
- [ ] upublicznić repo (lub osobne repo / PR do busycoq z samym dowodem Rocq)
- [ ] post na Discordzie bbchallenge (#bb6) z opisem, linkiem i wynikami
- [ ] recenzja, poprawki, aktualizacja listy holdoutów przez opiekunów

## Dziennik
- 2026-10-26: plan zapisany; start kroku 1.
- 2026-10-26: krok 1 i 2 zrobione (PROOF.md). Brak krótkiego opisu regułowego -> krok 3 idzie wariantem
  z weryfikowanym symulatorem; najpierw sprawdzić, co z busycoq (RWLAcc, Inductive, Compute) da się użyć.
- 2026-10-26: dysk C: był pełny (prawdopodobna przyczyna crasha) - stara kopia z Temp usunięta.
  busycoq zbudowany w Dockerze; ES_v3 (refleksyjny wykonawca symboliczny z regułami przesunięcia) wystarcza
  do lematów A: pierwszy lemat A udowodniony w Rocq.
- 2026-10-27: generator lematów A dla wszystkich węzłów. Pomysł na lematy B: es' (chk_sr) szuka reguł przesunięcia
  z kontekstem, więc konwersja może nie wymagać osobnej indukcji, jeśli liczba przemiatań nie zależy od M -
  `rocq/probe_lemmaB.py` to sprawdza (pierwsze uruchomienie przerwane przez brak pamięci; do powtórzenia z
  mniejszym limitem zdarzeń). Uwaga na pamięć: Docker (8 GB) + 6 procesów generatora naraz to za dużo.
