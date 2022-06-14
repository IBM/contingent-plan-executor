(define
    (domain order-pizza)
    (:requirements :strips :typing)
    (:types )
    (:constants )

    (:predicates
        (and
            (have_order)
            (maybe-have_order)
            (order_available)
            (have_location)
            (maybe-have_location)
            (have_payment_method)
            (maybe-have_payment_method)
            (have_card_number)
            (maybe-have_card_number)
            (goal)
            (can-do_ask-location)
            (can-do_ask-order)
            (can-do_ask-payment)
            (can-do_ask-card-number)
            (can-do_check-order-availability)
            (can-do_place-order)
            (can-do_clarify__ask-location)
            (can-do_clarify__ask-order)
            (can-do_clarify__ask-payment)
        )
    )
    (:action ask-location
        :parameters()
        :precondition
        (and
            (not (have_location))
            (not (maybe-have_location))
            (can-do_ask-location)
        )
        :effect
            (labeled-oneof validate-response
                (outcome valid
                    (and
                        (have_location)
                        (not (maybe-have_location))
                    )
                )
                (outcome unclear
                    (and
                        (not (have_location))
                        (not (maybe-have_location))
                    )
                )
            )
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
            (labeled-oneof validate-response
                (outcome valid
                    (and
                        (have_order)
                        (not (maybe-have_order))
                    )
                )
                (outcome unclear
                    (and
                        (not (have_order))
                        (not (maybe-have_order))
                    )
                )
            )
    )
    (:action ask-payment
        :parameters()
        :precondition
        (and
            (not (have_payment_method))
            (not (maybe-have_payment_method))
            (can-do_ask-payment)
        )
        :effect
            (labeled-oneof validate-response
                (outcome valid
                    (and
                        (have_payment_method)
                        (not (maybe-have_payment_method))
                    )
                )
                (outcome unclear
                    (and
                        (not (have_payment_method))
                        (not (maybe-have_payment_method))
                    )
                )
            )
    )
    (:action ask-card-number
        :parameters()
        :precondition
        (and
            (have_payment_method)
            (not (maybe-have_payment_method))
            (can-do_ask-card-number)
            (can-do_ask-card-number)
        )
        :effect
            (labeled-oneof validate-response
                (outcome valid
                    (and
                        (have_card_number)
                        (not (maybe-have_card_number))
                    )
                )
                (outcome unclear
                    (and
                        (not (have_card_number))
                        (not (maybe-have_card_number))
                    )
                )
            )
    )
    (:action check-order-availability
        :parameters()
        :precondition
        (and
            (have_order)
            (not (maybe-have_order))
            (can-do_check-order-availability)
        )
        :effect
            (labeled-oneof make-call
                (outcome in-stock
                )
                (outcome out-of-stock
                    (and
                        (not (have_order))
                        (not (maybe-have_order))
                    )
                )
                (outcome site-down
                )
            )
    )
    (:action place-order
        :parameters()
        :precondition
        (and
            (can-do_place-order)
            (can-do_place-order)
        )
        :effect
            (labeled-oneof make-call
                (outcome success
                    (and
                        (not (can-do_ask-location))
                        (not (can-do_ask-order))
                        (not (can-do_ask-payment))
                        (not (can-do_ask-card-number))
                        (not (can-do_check-order-availability))
                    )
                )
                (outcome site-down
                )
            )
    )
    (:action clarify__ask-location
        :parameters()
        :precondition
        (and
            (not (have_location))
            (not (maybe-have_location))
            (can-do_clarify__ask-location)
        )
        :effect
            (labeled-oneof yes-no
                (outcome confirm
                    (and
                        (have_location)
                        (not (maybe-have_location))
                    )
                )
                (outcome deny
                    (and
                        (not (have_entity))
                        (not (maybe-have_entity))
                    )
                )
            )
    )
    (:action clarify__ask-order
        :parameters()
        :precondition
        (and
            (not (have_order))
            (not (maybe-have_order))
            (can-do_clarify__ask-order)
        )
        :effect
            (labeled-oneof yes-no
                (outcome confirm
                    (and
                        (have_order)
                        (not (maybe-have_order))
                    )
                )
                (outcome deny
                    (and
                        (not (have_entity))
                        (not (maybe-have_entity))
                    )
                )
            )
    )
    (:action clarify__ask-payment
        :parameters()
        :precondition
        (and
            (not (have_payment_method))
            (not (maybe-have_payment_method))
            (can-do_clarify__ask-payment)
        )
        :effect
            (labeled-oneof yes-no
                (outcome confirm
                    (and
                        (have_payment_method)
                        (not (maybe-have_payment_method))
                    )
                )
                (outcome deny
                    (and
                        (not (have_entity))
                        (not (maybe-have_entity))
                    )
                )
            )
    )
)