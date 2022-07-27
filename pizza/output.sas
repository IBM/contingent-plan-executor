begin_version
3
end_version
begin_metric
0
end_metric
7
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
Atom have_drink()
NegatedAtom have_drink()
end_variable
begin_variable
var2
-1
2
Atom maybe-have_drink()
NegatedAtom maybe-have_drink()
end_variable
begin_variable
var3
-1
2
Atom have_order()
NegatedAtom have_order()
end_variable
begin_variable
var4
-1
2
Atom maybe-have_order()
NegatedAtom maybe-have_order()
end_variable
begin_variable
var5
-1
2
Atom have-message()
NegatedAtom have-message()
end_variable
begin_variable
var6
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
end_state
begin_goal
1
6 0
end_goal
23
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_found 
4
0 1
3 1
2 1
4 1
1
0 1 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-drink_maybe-found 
4
0 1
1 1
3 1
4 1
1
0 2 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-fallback 
4
1 1
3 1
2 1
4 1
2
0 0 1 0
0 5 -1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-order_found 
4
0 1
1 1
2 1
4 1
1
0 3 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-order_found-drink_found 
3
0 1
2 1
4 1
2
0 1 1 0
0 3 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-order_found-drink_maybe-found 
3
0 1
1 1
4 1
2
0 3 1 0
0 2 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-order_maybe-found 
4
0 1
1 1
3 1
2 1
1
0 4 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-order_maybe-found-drink_found 
3
0 1
3 1
2 1
2
0 1 1 0
0 4 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-slot-fill-EQ-order_maybe-found-drink_maybe-found 
3
0 1
1 1
3 1
2
0 2 1 0
0 4 1 0
1
end_operator
begin_operator
clarify__drink_DETDUP_validate-clarification-EQ-confirm 
1
0 1
2
0 1 1 0
0 2 0 1
1
end_operator
begin_operator
clarify__drink_DETDUP_validate-clarification-EQ-deny 
2
0 1
1 1
1
0 2 0 1
1
end_operator
begin_operator
clarify__drink_DETDUP_validate-clarification-EQ-fallback 
2
1 1
2 0
2
0 0 1 0
0 5 -1 0
1
end_operator
begin_operator
clarify__order_DETDUP_validate-clarification-EQ-confirm 
1
0 1
2
0 3 1 0
0 4 0 1
1
end_operator
begin_operator
clarify__order_DETDUP_validate-clarification-EQ-deny 
2
0 1
3 1
1
0 4 0 1
1
end_operator
begin_operator
clarify__order_DETDUP_validate-clarification-EQ-fallback 
2
3 1
4 0
2
0 0 1 0
0 5 -1 0
1
end_operator
begin_operator
complete_DETDUP_finish-EQ-assign-goal 
4
1 0
3 0
2 1
4 1
1
0 6 -1 0
1
end_operator
begin_operator
dialogue_statement_DETDUP_reset-EQ-lock 
0
2
0 0 0 1
0 5 0 1
1
end_operator
begin_operator
single_slot__drink_DETDUP_validate-clarification-EQ-fallback 
2
1 1
2 1
2
0 0 1 0
0 5 -1 0
1
end_operator
begin_operator
single_slot__drink_DETDUP_validate-clarification-EQ-fill-slot 
2
0 1
2 1
1
0 1 1 0
1
end_operator
begin_operator
single_slot__drink_DETDUP_validate-clarification-EQ-slot-unclear 
2
0 1
1 1
1
0 2 1 0
1
end_operator
begin_operator
single_slot__order_DETDUP_validate-clarification-EQ-fallback 
2
3 1
4 1
2
0 0 1 0
0 5 -1 0
1
end_operator
begin_operator
single_slot__order_DETDUP_validate-clarification-EQ-fill-slot 
2
0 1
4 1
1
0 3 1 0
1
end_operator
begin_operator
single_slot__order_DETDUP_validate-clarification-EQ-slot-unclear 
2
0 1
3 1
1
0 4 1 0
1
end_operator
0
