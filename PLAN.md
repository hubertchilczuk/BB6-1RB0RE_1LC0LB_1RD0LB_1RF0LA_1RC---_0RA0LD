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
- [ ] zainstalować Rocq/Coq, sklonować busycoq (ccz181078), zbudować i przejrzeć istniejące dowody BB6 (`verify/`)
- [ ] zapisać maszynę i reguły z kroku 1 jako lematy (shift rules / indukcja po licznikach)
- [ ] dowód twierdzenia `~ halts tm c0`
- [ ] jeśli krok 1 nie da zwartego opisu: plan B - certyfikat (lematy z `proof4.json`) + symulator symboliczny
      zweryfikowany w Rocq

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
