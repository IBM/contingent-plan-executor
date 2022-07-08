(define
    (domain order-pizza)
    (:requirements :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (have_order)
        (maybe-have_order)
        (goal)
        (can-do_ask-order)
    )
    (:action ask-order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (maybe-have_order))
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

                    )
                )
            )
    )
)