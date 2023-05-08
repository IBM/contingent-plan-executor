(define
    (domain day-planner)
    (:requirements         :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (know__location)
        (maybe-know__location)
        (know__phone_number)
        (maybe-know__phone_number)
        (know__cuisine)
        (maybe-know__cuisine)
        (know__have_allergy)
        (have_allergy)
        (know__food_restriction)
        (know__budget)
        (know__outing_type)
        (maybe-know__outing_type)
        (know__conflict)
        (conflict)
        (know__restaurant)
        (know__outing)
        (know__goal)
        (goal)
        (have-message)
        (force-statement)
        (allow_single_slot_outing_type)
        (allow_single_slot_budget)
        (forcing__get-allergy)
    )
    (:action get-have-allergy
        :parameters()
        :precondition
            (and
                (not (forcing__get-allergy))
                (not (know__have_allergy))
                (not (force-statement))
            )
        :effect
            (labeled-oneof         get-have-allergy__set-allergy
                (outcome indicate_allergy
                    (and
                        (know__have_allergy)
                        (have_allergy)
                        (forcing__get-allergy)
                    )
                )
                (outcome indicate_no_allergy
                    (and
                        (know__have_allergy)
                        (know__conflict)
                        (not (have_allergy))
                        (not (conflict))
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
    (:action get-allergy
        :parameters()
        :precondition
            (and
                (know__have_allergy)
                (have_allergy)
                (not (force-statement))
            )
        :effect
            (labeled-oneof         get-allergy__set-allergy
                (outcome update_allergy
                    (and
                        (not (forcing__get-allergy))
                        (know__food_restriction)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (not (forcing__get-allergy))
                        (force-statement)
                    )
                )
            )
    )
    (:action check-conflicts
        :parameters()
        :precondition
            (and
                (not (maybe-know__location))
                (not (forcing__get-allergy))
                (know__location)
                (not (know__conflict))
                (know__have_allergy)
                (have_allergy)
                (know__food_restriction)
                (know__cuisine)
                (not (force-statement))
                (not (maybe-know__cuisine))
            )
        :effect
            (labeled-oneof         check-conflicts__check-conflicts
                (outcome restriction-dessert
                    (and
                        (know__conflict)
                        (conflict)
                    )
                )
                (outcome restriction-mexican
                    (and
                        (know__conflict)
                        (conflict)
                    )
                )
                (outcome no-restriction-1
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
                (outcome no-restriction-2
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
                (outcome no-restriction-3
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
                (outcome no-restriction-4
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
            )
    )
    (:action reset-preferences
        :parameters()
        :precondition
            (and
                (know__conflict)
                (not (forcing__get-allergy))
                (conflict)
                (not (force-statement))
            )
        :effect
            (labeled-oneof         reset-preferences__reset
                (outcome reset-values
                    (and
                        (force-statement)
                        (not (know__cuisine))
                        (not (know__food_restriction))
                        (not (know__have_allergy))
                        (not (know__conflict))
                        (have-message)
                        (not (maybe-know__cuisine))
                    )
                )
            )
    )
    (:action set-restaurant
        :parameters()
        :precondition
            (and
                (know__conflict)
                (not (know__restaurant))
                (not (forcing__get-allergy))
                (not (conflict))
                (know__cuisine)
                (not (force-statement))
                (not (maybe-know__cuisine))
            )
        :effect
            (labeled-oneof         set-restaurant__assign_restaurant
                (outcome set-mexican
                    (and
                        (know__restaurant)
                    )
                )
                (outcome set-italian
                    (and
                        (know__restaurant)
                    )
                )
                (outcome set-chinese
                    (and
                        (know__restaurant)
                    )
                )
                (outcome set-dessert
                    (and
                        (know__restaurant)
                    )
                )
            )
    )
    (:action set-outing
        :parameters()
        :precondition
            (and
                (not (forcing__get-allergy))
                (know__budget)
                (know__outing_type)
                (not (maybe-know__outing_type))
                (not (force-statement))
            )
        :effect
            (labeled-oneof         set-outing__assign_outing
                (outcome set-club
                    (and
                        (know__outing)
                    )
                )
                (outcome set-library
                    (and
                        (know__outing)
                    )
                )
                (outcome set-theater
                    (and
                        (know__outing)
                    )
                )
                (outcome set-golf
                    (and
                        (know__outing)
                    )
                )
            )
    )
    (:action complete
        :parameters()
        :precondition
            (and
                (not (maybe-know__location))
                (not (forcing__get-allergy))
                (know__location)
                (know__phone_number)
                (not (maybe-know__phone_number))
                (know__restaurant)
                (know__outing)
                (not (force-statement))
            )
        :effect
            (labeled-oneof         complete__finish
                (outcome finish
                    (and
                        (goal)
                        (know__goal)
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
            (labeled-oneof         dialogue_statement__reset
                (outcome lock
                    (and
                        (not (have-message))
                        (not (force-statement))
                    )
                )
            )
    )
    (:action slot-fill__get-location
        :parameters()
        :precondition
            (and
                (not (forcing__get-allergy))
                (not (maybe-know__location))
                (not (force-statement))
                (not (know__location))
            )
        :effect
            (labeled-oneof         slot-fill__get-location__validate-slot-fill
                (outcome location_found
                    (and
                        (have-message)
                        (not (maybe-know__location))
                        (force-statement)
                        (know__location)
                    )
                )
                (outcome location_maybe-found
                    (and
                        (maybe-know__location)
                        (not (know__location))
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
    (:action clarify__location
        :parameters()
        :precondition
            (and
                (not (forcing__get-allergy))
                (maybe-know__location)
                (not (force-statement))
                (not (know__location))
            )
        :effect
            (labeled-oneof         clarify__location__validate-clarification
                (outcome confirm
                    (and
                        (have-message)
                        (not (maybe-know__location))
                        (force-statement)
                        (know__location)
                    )
                )
                (outcome deny
                    (and
                        (not (maybe-know__location))
                        (not (know__location))
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
    (:action slot-fill__get-phone_number
        :parameters()
        :precondition
            (and
                (not (know__phone_number))
                (not (forcing__get-allergy))
                (not (force-statement))
                (not (maybe-know__phone_number))
            )
        :effect
            (labeled-oneof         slot-fill__get-phone_number__validate-slot-fill
                (outcome phone_number_found
                    (and
                        (not (maybe-know__phone_number))
                        (know__phone_number)
                    )
                )
                (outcome phone_number_maybe-found
                    (and
                        (not (know__phone_number))
                        (maybe-know__phone_number)
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
    (:action clarify__phone_number
        :parameters()
        :precondition
            (and
                (not (know__phone_number))
                (not (forcing__get-allergy))
                (not (force-statement))
                (maybe-know__phone_number)
            )
        :effect
            (labeled-oneof         clarify__phone_number__validate-clarification
                (outcome confirm
                    (and
                        (not (maybe-know__phone_number))
                        (know__phone_number)
                    )
                )
                (outcome deny
                    (and
                        (not (know__phone_number))
                        (not (maybe-know__phone_number))
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
    (:action slot-fill__get-cuisine
        :parameters()
        :precondition
            (and
                (not (maybe-know__cuisine))
                (not (forcing__get-allergy))
                (not (force-statement))
                (not (know__cuisine))
            )
        :effect
            (labeled-oneof         slot-fill__get-cuisine__validate-slot-fill
                (outcome cuisine_found
                    (and
                        (know__cuisine)
                        (force-statement)
                        (have-message)
                        (not (maybe-know__cuisine))
                    )
                )
                (outcome cuisine_maybe-found
                    (and
                        (maybe-know__cuisine)
                        (not (know__cuisine))
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
    (:action clarify__cuisine
        :parameters()
        :precondition
            (and
                (maybe-know__cuisine)
                (not (forcing__get-allergy))
                (not (force-statement))
                (not (know__cuisine))
            )
        :effect
            (labeled-oneof         clarify__cuisine__validate-clarification
                (outcome confirm
                    (and
                        (know__cuisine)
                        (force-statement)
                        (have-message)
                        (not (maybe-know__cuisine))
                    )
                )
                (outcome deny
                    (and
                        (not (maybe-know__cuisine))
                        (not (know__cuisine))
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
    (:action slot-fill__get_outing
        :parameters()
        :precondition
            (and
                (not (forcing__get-allergy))
                (not (know__outing_type))
                (not (maybe-know__outing_type))
                (not (force-statement))
                (not (know__budget))
            )
        :effect
            (labeled-oneof         slot-fill__get_outing__validate-slot-fill
                (outcome budget_found-outing_type_found
                    (and
                        (not (maybe-know__outing_type))
                        (know__budget)
                        (know__outing_type)
                    )
                )
                (outcome budget_found-outing_type_maybe-found
                    (and
                        (not (know__outing_type))
                        (maybe-know__outing_type)
                        (know__budget)
                    )
                )
                (outcome budget_found
                    (and
                        (have-message)
                        (allow_single_slot_outing_type)
                        (force-statement)
                        (know__budget)
                    )
                )
                (outcome outing_type_found
                    (and
                        (force-statement)
                        (know__outing_type)
                        (allow_single_slot_budget)
                        (not (maybe-know__outing_type))
                        (have-message)
                    )
                )
                (outcome outing_type_maybe-found
                    (and
                        (not (know__outing_type))
                        (allow_single_slot_budget)
                        (maybe-know__outing_type)
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
    (:action single_slot__outing_type
        :parameters()
        :precondition
            (and
                (not (forcing__get-allergy))
                (not (know__outing_type))
                (allow_single_slot_outing_type)
                (not (maybe-know__outing_type))
                (not (force-statement))
            )
        :effect
            (labeled-oneof         single_slot__outing_type__validate-slot-fill
                (outcome fill-slot
                    (and
                        (have-message)
                        (not (maybe-know__outing_type))
                        (force-statement)
                        (know__outing_type)
                    )
                )
                (outcome slot-unclear
                    (and
                        (not (know__outing_type))
                        (maybe-know__outing_type)
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
    (:action single_slot__budget
        :parameters()
        :precondition
            (and
                (allow_single_slot_budget)
                (not (forcing__get-allergy))
                (not (force-statement))
                (not (know__budget))
            )
        :effect
            (labeled-oneof         single_slot__budget__validate-slot-fill
                (outcome fill-slot
                    (and
                        (have-message)
                        (force-statement)
                        (know__budget)
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
    (:action clarify__outing_type
        :parameters()
        :precondition
            (and
                (not (know__outing_type))
                (not (forcing__get-allergy))
                (maybe-know__outing_type)
                (not (force-statement))
            )
        :effect
            (labeled-oneof         clarify__outing_type__validate-clarification
                (outcome confirm
                    (and
                        (have-message)
                        (not (maybe-know__outing_type))
                        (force-statement)
                        (know__outing_type)
                    )
                )
                (outcome deny
                    (and
                        (allow_single_slot_outing_type)
                        (not (know__outing_type))
                        (not (maybe-know__outing_type))
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