begin_version
3
end_version
begin_metric
0
end_metric
9
begin_variable
var0
-1
2
Atom have_side()
NegatedAtom have_side()
end_variable
begin_variable
var1
-1
2
Atom have_order()
NegatedAtom have_order()
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
Atom forcing__ask-drink()
NegatedAtom forcing__ask-drink()
end_variable
begin_variable
var5
-1
2
Atom maybe-have_order()
NegatedAtom maybe-have_order()
end_variable
begin_variable
var6
-1
2
Atom force-statement()
NegatedAtom force-statement()
end_variable
begin_variable
var7
-1
2
Atom have-message()
NegatedAtom have-message()
end_variable
begin_variable
var8
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
end_state
begin_goal
1
8 0
end_goal
15
begin_operator
ask-drink_DETDUP_validate-response-EQ-fallback 
4
2 1
1 0
3 1
5 1
2
0 6 1 0
0 7 -1 0
1
end_operator
begin_operator
ask-drink_DETDUP_validate-response-EQ-unclear 
4
6 1
2 1
1 0
5 1
1
0 3 1 0
1
end_operator
begin_operator
ask-drink_DETDUP_validate-response-EQ-valid 
4
6 1
1 0
3 1
5 1
2
0 4 -1 1
0 2 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-response-EQ-fallback 
3
4 1
1 1
5 1
2
0 6 1 0
0 7 -1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-response-EQ-unclear 
3
6 1
4 1
1 1
1
0 5 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-response-EQ-valid 
2
6 1
5 1
2
0 4 1 0
0 1 1 0
1
end_operator
begin_operator
ask-side_DETDUP_validate-side-EQ-fallback 
4
4 1
1 0
0 1
5 1
2
0 6 1 0
0 7 -1 0
1
end_operator
begin_operator
ask-side_DETDUP_validate-side-EQ-valid 
4
6 1
4 1
1 0
5 1
2
0 8 -1 0
0 0 1 0
1
end_operator
begin_operator
clarify__ask-drink_DETDUP_validate-clarification-EQ-confirm 
1
6 1
3
0 4 -1 1
0 2 1 0
0 3 0 1
1
end_operator
begin_operator
clarify__ask-drink_DETDUP_validate-clarification-EQ-deny 
2
6 1
2 1
1
0 3 0 1
1
end_operator
begin_operator
clarify__ask-drink_DETDUP_validate-clarification-EQ-fallback 
2
2 1
3 0
2
0 6 1 0
0 7 -1 0
1
end_operator
begin_operator
clarify__ask-order_DETDUP_validate-clarification-EQ-confirm 
2
6 1
4 1
2
0 1 1 0
0 5 0 1
1
end_operator
begin_operator
clarify__ask-order_DETDUP_validate-clarification-EQ-deny 
3
6 1
4 1
1 1
1
0 5 0 1
1
end_operator
begin_operator
clarify__ask-order_DETDUP_validate-clarification-EQ-fallback 
3
4 1
1 1
5 0
2
0 6 1 0
0 7 -1 0
1
end_operator
begin_operator
dialogue_statement_DETDUP_reset-EQ-lock 
0
2
0 6 0 1
0 7 0 1
1
end_operator
0
