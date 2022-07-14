(define
    (domain order-pizza)
    (:requirements :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (have_order)
        (maybe-have_order)
        (goal)
        (have-message)
        (force-statement)
        (can-do_ask-order)
        (can-do_dialogue_statement)
    )
    (:action ask-order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (maybe-have_order))
                (not (force-statement))
                (can-do_ask-order)
            )
        :effect
            (labeled-oneof validate-order
                (outcome valid
                    (and
                        (have_order)
                        (not (maybe-have_order))
                        (goal)
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
)