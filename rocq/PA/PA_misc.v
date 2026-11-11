From BusyCoq Require Import Individual62.
From BB6F Require Import F Dom.
Require Import String.
Require Start D_60462068_1.
Print Assumptions Start.start.
Print Assumptions D_60462068_1.F_60462068_1_descent.
Print Assumptions multistep_nonhalt.
Print Assumptions progress_nonhalt.
Print Assumptions evstep_trans.
Print Assumptions Dom.
Definition tm := TM_from_str "1RB0RE_1LC0LB_1RD0LB_1RF0LA_1RC---_0RA0LD".
Print Assumptions tm.
