(define
    (domain order-pizza)
    (:requirements :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (have_order)
        (maybe-have_order)
        (have_drink)
        (maybe-have_drink)
        (goal)
        (have-message)
        (force-statement)
    )
    (:action ask-order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (force-statement))
                (not (have_drink))
                (not (maybe-have_order))
                (not (maybe-have_drink))
            )
        :effect
            (labeled-oneof validate-slot-fill
                (outcome order_found-drink_found
                    (and
                        (have_order)
                        (not (maybe-have_order))
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome order_found-drink_maybe-found
                    (and
                        (have_order)
                        (not (maybe-have_order))
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome order_found
                    (and
                        (have_order)
                        (not (maybe-have_order))
                    )
                )
                (outcome order_maybe-found-drink_found
                    (and
                        (not (have_order))
                        (maybe-have_order)
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome order_maybe-found-drink_maybe-found
                    (and
                        (not (have_order))
                        (maybe-have_order)
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome order_maybe-found
                    (and
                        (not (have_order))
                        (maybe-have_order)
                    )
                )
                (outcome drink_found
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome drink_maybe-found
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action complete
        :parameters()
        :precondition
            (and
                (not (maybe-have_drink))
                (not (maybe-have_order))
                (have_order)
                (have_drink)
            )
        :effect
            (labeled-oneof finish
                (outcome assign-goal
                    (and
                        (goal)
                    )
                )
            )
    )
    (:action dialogue_statement
        :parameters()
        :precondition
            (and
                (have-message)
                (force-statement)
            )
        :effect
            (labeled-oneof reset
                (outcome lock
                    (and
                        (not (have-message))
                        (not (force-statement))
                    )
                )
            )
    )
    (:action clarify__order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (force-statement))
                (maybe-have_order)
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome confirm
                    (and
                        (have_order)
                        (not (maybe-have_order))
                    )
                )
                (outcome deny
                    (and
                        (not (have_order))
                        (not (maybe-have_order))
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action clarify__drink
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (have_drink))
                (maybe-have_drink)
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome confirm
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome deny
                    (and
                        (not (have_drink))
                        (not (maybe-have_drink))
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action single_slot__order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (maybe-have_order))
                (not (force-statement))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome fill-slot
                    (and
                        (have_order)
                        (not (maybe-have_order))
                    )
                )
                (outcome slot-unclear
                    (and
                        (not (have_order))
                        (maybe-have_order)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action single_slot__drink
        :parameters()
        :precondition
            (and
                (not (maybe-have_drink))
                (not (force-statement))
                (not (have_drink))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome fill-slot
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome slot-unclear
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
)