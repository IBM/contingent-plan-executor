begin_version
3
end_version
begin_metric
0
end_metric
6
begin_variable
var0
-1
2
Atom have_drink()
NegatedAtom have_drink()
end_variable
begin_variable
var1
-1
2
Atom have_pizza_flavour()
NegatedAtom have_pizza_flavour()
end_variable
begin_variable
var2
-1
2
Atom have_side()
NegatedAtom have_side()
end_variable
begin_variable
var3
-1
2
Atom force-statement()
NegatedAtom force-statement()
end_variable
begin_variable
var4
-1
2
Atom have-message()
NegatedAtom have-message()
end_variable
begin_variable
var5
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
end_state
begin_goal
1
5 0
end_goal
4
begin_operator
complete_DETDUP_finish-EQ-assign-goal 
3
0 0
1 0
2 0
1
0 5 -1 0
1
end_operator
begin_operator
dialogue_statement_DETDUP_reset-EQ-lock 
0
2
0 3 0 1
0 4 0 1
1
end_operator
begin_operator
force-all_DETDUP_validate-EQ-fallback 
3
0 1
1 1
2 1
2
0 3 1 0
0 4 -1 0
1
end_operator
begin_operator
force-all_DETDUP_validate-EQ-valid 
1
3 1
3
0 0 1 0
0 1 1 0
0 2 1 0
1
end_operator
0
