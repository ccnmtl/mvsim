Feature: Manipulate State

    Scenario: manipulate_state.feature 2. View State
        Using selenium
        Given I am not logged in
        When I access the url "/"
        Then I am at the Log In page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        When I access the url "/state/2/"
        Then I see "Alternate State"

        And I do not see "The variables and coefficients cannot be changed."
        And there is a submit button

        # Integer
        And I see "Adult Effort"
        And the value for "adult_effort" is "12"

        # Float
        And I see "Avg Cotton Yield"
        And the value for "avg_cotton_yield" is "0.1"

        # Multi-value fields
        And I see "Available Improvements"
        And the values for "Available Improvements" are "road,electricity,sanitation,water_pump,irrigation,clinic,meals"

        Finished using Selenium


    Scenario Outline: manipulate_state.feature 3. Edit Integer Value
        Using selenium
        Given I am not logged in
        When I access the url "/"
        Then I am at the Log In page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        Then I am at the Home page

        When I access the url "/state/2/"
        Then I see "Alternate State"

        Then I sort by "<sort_order>"

        And I see "Adult Effort"
        And the value for "adult_effort" is "12"

        # Invalid string value
        When I type "foo" for adult_effort
        And I submit the state form
        Then I see ""foo" is not a number"
        And I see "Validation failed"

        # Invalid float value
        When I type "2.2" for adult_effort
        And I submit the state form
        Then I see ""2.2" is not a number"
        And I see "Validation failed"

        # Valid integer value
        When I type "13" for adult_effort
        And I submit the state form
        Then the value for "adult_effort" is "13"
        And I see "Your changes were saved"

        When I type "12" for adult_effort
        And I submit the state form
        Then the value for "adult_effort" is "12"
        And I see "Your changes were saved"

        Finished using Selenium

    Examples:
        | sort_order  |
        | Name        |
        | Type        |

    Scenario Outline: manipulate_state.feature 4. Edit Float Value
        Using selenium
        Given I am not logged in
        When I access the url "/"
        Then I am at the Log In page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        Then I am at the Home page

        When I access the url "/state/2/"
        Then I see "Alternate State"

        And I see "Avg Cotton Yield"
        And the value for "avg_cotton_yield" is "0.1"

        # Invalid string value
        When I type "foo" for avg_cotton_yield
        And I submit the state form
        Then I see ""foo" is not a number"
        And I see "Validation failed"

        # Valid integer value
        When I type "2" for avg_cotton_yield
        And I submit the state form
        Then the value for "avg_cotton_yield" is "2.0"
        And I see "Your changes were saved"

        # Valid float value
        When I type "0.1" for avg_cotton_yield
        And I submit the state form
        Then the value for "avg_cotton_yield" is "0.1"
        And I see "Your changes were saved"

        Finished using Selenium

    Examples:
        | sort_order  |
        | Name        |
        | Type        |

    Scenario Outline: manipulate_state.feature 5. Edit several values
        Using selenium
        Given I am not logged in
        When I access the url "/"
        Then I am at the Log In page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        Then I am at the Home page

        When I access the url "/state/2/"
        Then I see "Alternate State"

        I type "2" for avg_cotton_yield
        and I type "13" for adult_effort
        and I type "25000.2500" for fish_k
        and I type ".75" for mortality1
        and I type "500000" for family_needs
        and I type "0.2" for microfinance_amount_due

        When I submit the state form
        Then the value for "avg_cotton_yield" is "2.0"
        And the value for "adult_effort" is "13"
        And the value for "fish_k" is "25000.25"
        And the value for "mortality1" is "0.75"
        And the value for "family_needs" is "500000.0"
        And the value for "microfinance_amount_due" is "0.2"
        And I see "Your changes were saved"

        # Verify some random values
        The value for "wood_price" is "6.0"
        And the value for "wood_stock_warn_threshold" is "0.33"
        And the value for "w_subsistence" is "425.0"
        And the values for "Available Improvements" are "road,electricity,sanitation,water_pump,irrigation,clinic,meals"
        And the value for "avg_family_size" is "4"
        And the value for "avg_fishing_yield" is "1.1"
        And the value for "avg_maize_yield" is "1.0"
        And the value for "avg_precipitation" is "900.0"
        And the value for "avg_small_business_yield" is "100.0"
        And the value for "avg_water_yield" is "2.0"
        And the value for "avg_wood_yield" is "0.9"
        And the value for "base_infection_rate" is "0.003"
        And the value for "bednet_infection_modifier" is "-0.5"
        And the value for "birth_rate" is "0.02"
        And the value for "boat_coeff" is "2.0"
        And the value for "chance_of_getting_the_flu" is "0.05"
        And the value for "child_1_effort" is "0"
        And the value for "child_2_effort" is "4"
        And the value for "child_3_effort" is "8"
        And the values for "Child Genders" are "Female,Male,Female,Male,Female,Male,Female,Male,Female,Male,Female,Male,Female,Male,Female,Male"
        And the values for "Child Names" are "Damba,Mamadou,Awa,Yao,Jeanne,Amadou,Mariam,Samuel,Aminata,Kuoakou,Kady,Jean"
        And the value for "wood_fuel" is "0.0"
        And the value for "wood_stock" is "80000"
        And the value for "amount_calories" is "900000.0"
        And the value for "cost_to_market" is "0.0"
        And the values for "Ages" are "15,15"
        And the value for "cash" is "1000.0"
        And the value for "clinic" is "true"
        And the value for "cotton_income" is "0.0"
        And the value for "effort_water" is "0"
        And the value for "electricity" is "true"
        And the value for "epidemic" is "true"
        And the value for "effort_fishing" is "0"
        And the value for "expenditure" is "0.0"
        And the value for "family_needs" is "500000.0"
        And the value for "small_business_income" is "0.0"
        And the value for "small_business_investment" is "0.0"

        Finished using Selenium
     Examples:
        | sort_order  |
        | Name        |
        | Type        |
