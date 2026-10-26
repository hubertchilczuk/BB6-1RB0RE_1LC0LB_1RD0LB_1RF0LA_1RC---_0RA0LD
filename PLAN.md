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
- [ ] zbadać trajektorię na poziomie cykli: które węzły i stany naprawdę występują, jak zmieniają się (N, M, k)
- [ ] znaleźć kodowanie konfiguracji jako kilka liczników i małą liczbę reguł przejścia (jak w dowodach busycoq)
- [ ] sprawdzić reguły symulacją (`fsim`) na wielu instancjach
- [ ] udowodnić niezatrzymywanie się z reguł: niezmiennik + indukcja (najpierw na papierze / w Pythonie)

### 2. Opis dla ludzi (`PROOF.md`)
- [ ] notacja konfiguracji, reguły, schemat dowodu, skąd bierze się nieskończony wzrost
- [ ] powiązanie z dowodem komputerowym (`proof4.json`, `verify4`) jako niezależnym potwierdzeniem

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
