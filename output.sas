begin_version
3
end_version
begin_metric
0
end_metric
15
begin_variable
var0
-1
2
Atom have_location()
NegatedAtom have_location()
end_variable
begin_variable
var1
-1
2
Atom maybe-have_location()
NegatedAtom maybe-have_location()
end_variable
begin_variable
var2
-1
2
Atom order_available()
NegatedAtom order_available()
end_variable
begin_variable
var3
-1
2
Atom maybe-have_order()
NegatedAtom maybe-have_order()
end_variable
begin_variable
var4
-1
2
Atom have_order()
NegatedAtom have_order()
end_variable
begin_variable
var5
-1
2
Atom can-do_ask-card-number()
NegatedAtom can-do_ask-card-number()
end_variable
begin_variable
var6
-1
2
Atom can-do_ask-location()
NegatedAtom can-do_ask-location()
end_variable
begin_variable
var7
-1
2
Atom can-do_ask-order()
NegatedAtom can-do_ask-order()
end_variable
begin_variable
var8
-1
2
Atom can-do_ask-payment()
NegatedAtom can-do_ask-payment()
end_variable
begin_variable
var9
-1
2
Atom can-do_check-order-availability()
NegatedAtom can-do_check-order-availability()
end_variable
begin_variable
var10
-1
2
Atom have_payment_method()
NegatedAtom have_payment_method()
end_variable
begin_variable
var11
-1
2
Atom maybe-have_payment_method()
NegatedAtom maybe-have_payment_method()
end_variable
begin_variable
var12
-1
2
Atom have_card_number()
NegatedAtom have_card_number()
end_variable
begin_variable
var13
-1
2
Atom maybe-have_card_number()
NegatedAtom maybe-have_card_number()
end_variable
begin_variable
var14
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
0
0
0
0
0
1
1
1
1
1
end_state
begin_goal
1
14 0
end_goal
17
begin_operator
ask-card-number_DETDUP_validate-response-EQ-unclear 
3
5 0
10 0
11 1
2
0 12 -1 1
0 13 -1 0
1
end_operator
begin_operator
ask-card-number_DETDUP_validate-response-EQ-valid 
3
5 0
10 0
11 1
2
0 12 -1 0
0 13 -1 1
1
end_operator
begin_operator
ask-location_DETDUP_validate-response-EQ-unclear 
2
6 0
0 1
1
0 1 1 0
1
end_operator
begin_operator
ask-location_DETDUP_validate-response-EQ-valid 
2
6 0
1 1
1
0 0 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-response-EQ-unclear 
2
7 0
4 1
1
0 3 1 0
1
end_operator
begin_operator
ask-order_DETDUP_validate-response-EQ-valid 
2
7 0
3 1
1
0 4 1 0
1
end_operator
begin_operator
ask-payment_DETDUP_validate-response-EQ-unclear 
6
8 0
0 0
4 0
10 1
1 1
3 1
1
0 11 1 0
1
end_operator
begin_operator
ask-payment_DETDUP_validate-response-EQ-valid 
6
8 0
0 0
4 0
1 1
3 1
11 1
1
0 10 1 0
1
end_operator
begin_operator
check-order-availability_DETDUP_make-call-EQ-in-stock 
3
9 0
4 0
3 1
1
0 2 -1 0
1
end_operator
begin_operator
check-order-availability_DETDUP_make-call-EQ-out-of-stock 
2
9 0
3 1
1
0 4 0 1
1
end_operator
begin_operator
clarify__ask-location_DETDUP_yes-no-EQ-confirm 
0
2
0 0 1 0
0 1 0 1
1
end_operator
begin_operator
clarify__ask-location_DETDUP_yes-no-EQ-deny 
1
0 1
1
0 1 0 1
1
end_operator
begin_operator
clarify__ask-order_DETDUP_yes-no-EQ-confirm 
0
2
0 4 1 0
0 3 0 1
1
end_operator
begin_operator
clarify__ask-order_DETDUP_yes-no-EQ-deny 
1
4 1
1
0 3 0 1
1
end_operator
begin_operator
clarify__ask-payment_DETDUP_yes-no-EQ-confirm 
0
2
0 10 1 0
0 11 0 1
1
end_operator
begin_operator
clarify__ask-payment_DETDUP_yes-no-EQ-deny 
1
10 1
1
0 11 0 1
1
end_operator
begin_operator
place-order_DETDUP_make-call-EQ-success 
5
12 0
4 0
13 1
3 1
2 0
6
0 5 -1 1
0 6 -1 1
0 7 -1 1
0 8 -1 1
0 9 -1 1
0 14 -1 0
1
end_operator
0
