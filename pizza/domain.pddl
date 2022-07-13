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
        (can-do_agent_fallback)
    )
    (:action ask-order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (maybe-have_order))
                (not (can-do_agent_fallback))
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
                        (can-do_agent_fallback)
                    )
                )
            )
    )
    (:action agent_fallback
        :parameters()
        :precondition
            (and
                (can-do_agent_fallback)
            )
        :effect
            (labeled-oneof reset
                (outcome lock
                    (and
                        (not (can-do_agent_fallback))
                    )
                )
            )
    )
)