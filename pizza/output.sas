begin_version
3
end_version
begin_metric
0
end_metric
13
begin_variable
var0
-1
2
Atom force-statement()
NegatedAtom force-statement()
end_variable
begin_variable
var1
-1
2
Atom have-message()
NegatedAtom have-message()
end_variable
begin_variable
var2
-1
2
Atom have_drink()
NegatedAtom have_drink()
end_variable
begin_variable
var3
-1
2
Atom maybe-have_drink()
NegatedAtom maybe-have_drink()
end_variable
begin_variable
var4
-1
2
Atom have_pizza_flavour()
NegatedAtom have_pizza_flavour()
end_variable
begin_variable
var5
-1
2
Atom maybe-have_pizza_flavour()
NegatedAtom maybe-have_pizza_flavour()
end_variable
begin_variable
var6
-1
2
Atom have_side()
NegatedAtom have_side()
end_variable
begin_variable
var7
-1
2
Atom maybe-have_side()
NegatedAtom maybe-have_side()
end_variable
begin_variable
var8
-1
2
Atom allow_single_slot_drink()
NegatedAtom allow_single_slot_drink()
end_variable
begin_variable
var9
-1
2
Atom allow_single_slot_pizza_flavour()
NegatedAtom allow_single_slot_pizza_flavour()
end_variable
begin_variable
var10
-1
2
Atom allow_single_slot_side()
NegatedAtom allow_single_slot_side()
end_variable
begin_variable
var11
-1
2
Atom maybe_pizza()
NegatedAtom maybe_pizza()
end_variable
begin_variable
var12
-1
2
Atom goal()
NegatedAtom goal()
end_variable
0
begin_state
1
1
1
1
1
1
1
1
1
1
1
1
1
end_state
begin_goal
1
12 0
end_goal
47
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_found 
5
4 1
6 1
3 1
5 1
7 1
5
0 9 -1 0
0 10 -1 0
0 0 1 0
0 1 -1 0
0 2 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_found-side_found 
5
0 1
4 1
3 1
5 1
7 1
3
0 9 -1 0
0 2 1 0
0 6 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_found-side_maybe-found 
5
0 1
4 1
6 1
3 1
5 1
3
0 9 -1 0
0 2 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_maybe-found 
6
0 1
2 1
4 1
6 1
5 1
7 1
3
0 9 -1 0
0 10 -1 0
0 3 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_maybe-found-side_found 
5
0 1
2 1
4 1
5 1
7 1
3
0 9 -1 0
0 6 1 0
0 3 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_maybe-found-side_maybe-found 
5
0 1
2 1
4 1
6 1
5 1
3
0 9 -1 0
0 3 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-fallback 
6
2 1
4 1
6 1
3 1
5 1
7 1
2
0 0 1 0
0 1 -1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found 
5
2 1
6 1
3 1
5 1
7 1
5
0 8 -1 0
0 10 -1 0
0 0 1 0
0 1 -1 0
0 4 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-drink_found 
5
0 1
6 1
3 1
5 1
7 1
3
0 10 -1 0
0 2 1 0
0 4 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-drink_found-side_found 
4
0 1
3 1
5 1
7 1
3
0 2 1 0
0 4 1 0
0 6 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-drink_found-side_maybe-found 
4
0 1
6 1
3 1
5 1
3
0 2 1 0
0 4 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-drink_maybe-found 
5
0 1
2 1
6 1
5 1
7 1
3
0 10 -1 0
0 4 1 0
0 3 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-drink_maybe-found-side_found 
4
0 1
2 1
5 1
7 1
3
0 4 1 0
0 6 1 0
0 3 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-drink_maybe-found-side_maybe-found 
4
0 1
2 1
6 1
5 1
3
0 4 1 0
0 3 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-side_found 
5
0 1
2 1
3 1
5 1
7 1
3
0 8 -1 0
0 4 1 0
0 6 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_found-side_maybe-found 
5
0 1
2 1
6 1
3 1
5 1
3
0 8 -1 0
0 4 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found 
6
0 1
2 1
4 1
6 1
3 1
7 1
4
0 8 -1 0
0 10 -1 0
0 5 1 0
0 11 -1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-drink_found 
5
0 1
4 1
6 1
3 1
7 1
3
0 10 -1 0
0 2 1 0
0 5 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-drink_found-side_found 
4
0 1
4 1
3 1
7 1
3
0 2 1 0
0 6 1 0
0 5 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-drink_found-side_maybe-found 
4
0 1
4 1
6 1
3 1
3
0 2 1 0
0 5 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-drink_maybe-found 
5
0 1
2 1
4 1
6 1
7 1
3
0 10 -1 0
0 3 1 0
0 5 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-drink_maybe-found-side_found 
4
0 1
2 1
4 1
7 1
3
0 6 1 0
0 3 1 0
0 5 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-drink_maybe-found-side_maybe-found 
4
0 1
2 1
4 1
6 1
3
0 3 1 0
0 5 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-side_found 
5
0 1
2 1
4 1
3 1
7 1
3
0 8 -1 0
0 6 1 0
0 5 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-pizza_flavour_maybe-found-side_maybe-found 
5
0 1
2 1
4 1
6 1
3 1
3
0 8 -1 0
0 5 1 0
0 7 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-side_found 
5
2 1
4 1
3 1
5 1
7 1
5
0 8 -1 0
0 9 -1 0
0 0 1 0
0 1 -1 0
0 6 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-side_maybe-found 
6
0 1
2 1
4 1
6 1
3 1
5 1
3
0 8 -1 0
0 9 -1 0
0 7 1 0
1
end_operator
begin_operator
clarify__drink_DETDUP_validate-clarification-EQ-confirm 
1
0 1
2
0 2 1 0
0 3 0 1
1
end_operator
begin_operator
clarify__drink_DETDUP_validate-clarification-EQ-deny 
2
0 1
2 1
2
0 8 -1 0
0 3 0 1
1
end_operator
begin_operator
clarify__drink_DETDUP_validate-clarification-EQ-fallback 
2
2 1
3 0
2
0 0 1 0
0 1 -1 0
1
end_operator
begin_operator
clarify__pizza_flavour_DETDUP_validate-clarification-EQ-confirm 
1
0 1
2
0 4 1 0
0 5 0 1
1
end_operator
begin_operator
clarify__pizza_flavour_DETDUP_validate-clarification-EQ-deny 
2
0 1
4 1
2
0 9 -1 0
0 5 0 1
1
end_operator
begin_operator
clarify__pizza_flavour_DETDUP_validate-clarification-EQ-fallback 
2
4 1
5 0
2
0 0 1 0
0 1 -1 0
1
end_operator
begin_operator
clarify__side_DETDUP_validate-clarification-EQ-confirm 
1
0 1
2
0 6 1 0
0 7 0 1
1
end_operator
begin_operator
clarify__side_DETDUP_validate-clarification-EQ-deny 
2
0 1
6 1
2
0 10 -1 0
0 7 0 1
1
end_operator
begin_operator
clarify__side_DETDUP_validate-clarification-EQ-fallback 
2
6 1
7 0
2
0 0 1 0
0 1 -1 0
1
end_operator
begin_operator
complete_DETDUP_finish-EQ-assign-goal 
6
2 0
4 0
6 0
3 1
5 1
7 1
1
0 12 -1 0
1
end_operator
begin_operator
dialogue_statement_DETDUP_reset-EQ-lock 
0
2
0 0 0 1
0 1 0 1
1
end_operator
begin_operator
single_slot__drink_DETDUP_validate-slot-fill-EQ-fallback 
3
8 0
2 1
3 1
2
0 0 1 0
0 1 -1 0
1
end_operator
begin_operator
single_slot__drink_DETDUP_validate-slot-fill-EQ-fill-slot 
1
3 1
4
0 8 0 1
0 0 1 0
0 1 -1 0
0 2 1 0
1
end_operator
begin_operator
single_slot__drink_DETDUP_validate-slot-fill-EQ-slot-unclear 
3
8 0
0 1
2 1
1
0 3 1 0
1
end_operator
begin_operator
single_slot__pizza_flavour_DETDUP_validate-slot-fill-EQ-fallback 
3
9 0
4 1
5 1
2
0 0 1 0
0 1 -1 0
1
end_operator
begin_operator
single_slot__pizza_flavour_DETDUP_validate-slot-fill-EQ-fill-slot 
1
5 1
4
0 9 0 1
0 0 1 0
0 1 -1 0
0 4 1 0
1
end_operator
begin_operator
single_slot__pizza_flavour_DETDUP_validate-slot-fill-EQ-slot-unclear 
3
9 0
0 1
4 1
1
0 5 1 0
1
end_operator
begin_operator
single_slot__side_DETDUP_validate-slot-fill-EQ-fallback 
3
10 0
6 1
7 1
2
0 0 1 0
0 1 -1 0
1
end_operator
begin_operator
single_slot__side_DETDUP_validate-slot-fill-EQ-fill-slot 
1
7 1
4
0 10 0 1
0 0 1 0
0 1 -1 0
0 6 1 0
1
end_operator
begin_operator
single_slot__side_DETDUP_validate-slot-fill-EQ-slot-unclear 
3
10 0
0 1
6 1
1
0 7 1 0
1
end_operator
0
