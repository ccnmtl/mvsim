Feature: Manipulate State

    Scenario: manipulate_state.feature 1. View State
        Using selenium        
        When I access the url "/"
        Then I am at the log in page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        Then I see "Select a Course"
        And there is a "Test Course" link
        
        When I click the "Test Course" link
        Then I am at the Home page
        
        When I access the url "/state/1/"
        Then I see "Default Starting State"
        
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
        
    Scenario: manipulate_state.feature 2. Edit Integer Value
        Using selenium
        Given I am not logged in        
        When I access the url "/"
        Then I am at the log in page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        Then I see "Select a Course"
        And there is a "Test Course" link
        
        When I click the "Test Course" link
        Then I am at the Home page
        
        When I access the url "/state/1/"
        Then I see "Default Starting State"
        
        And I see "Adult Effort"
        And the value for "adult_effort" is "12"
        
        # Invalid string value
        When I type "foo" for adult_effort
        And I click the submit button        
        Then I see ""foo" is not a number"
        
        # Invalid float value
        When I type "2.2" for adult_effort
        And I click the submit button        
        Then I see ""2.2" is not a number"
        
        # Valid integer value
        When I type "13" for adult_effort
        And I click the submit button
        Then the value for "adult_effort" is "13"    
        Finished using Selenium
        
    Scenario: manipulate_state.feature 3. Edit Float Value
        Using selenium
        Given I am not logged in        
        When I access the url "/"
        Then I am at the log in page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        Then I see "Select a Course"
        And there is a "Test Course" link
        
        When I click the "Test Course" link
        Then I am at the Home page
        
        When I access the url "/state/1/"
        Then I see "Default Starting State"
        
        And I see "Avg Cotton Yield"
        And the value for "avg_cotton_yield" is "0.1"
        
        # Invalid string value
        When I type "foo" for avg_cotton_yield
        And I click the submit button        
        Then I see ""foo" is not a number"
        
        # Valid integer value
		When I type "2" for avg_cotton_yield
        And I click the submit button
        Then the value for "avg_cotton_yield" is "2.0"    
                
        # Valid float value
		When I type "0.2" for avg_cotton_yield
        And I click the submit button
        Then the value for "avg_cotton_yield" is "0.2"  
          
        Finished using Selenium

        
	Scenario: manipulate_state.feature 4. Edit several values
        Using selenium
        Given I am not logged in        
        When I access the url "/"
        Then I am at the log in page
        When I type "admin" for username
        When I type "admin" for password
        When I log in
        Then I see "Select a Course"
        And there is a "Test Course" link
        
        When I click the "Test Course" link
        Then I am at the Home page
        
        When I access the url "/state/1/"
        Then I see "Default Starting State"
        
        I type "2" for avg_cotton_yield
        and I type "13" for adult_effort
        and I type "25000.25" for fish_k
        and I type "0.75" for mortality1
        and I type "500000.0" for family_needs
        and I type "0.2" for microfinance_amount_due
        
        When I click the submit button
        Then the value for "avg_cotton_yield" is "2.0"
        And the value for "adult_effort" is "13"
        And the value for "fish_k" is "25000.25"
        And the value for "mortality1" is "0.75"
        And the value for "family_needs" is "500000.0"    
        And the value for "microfinance_amount_due" is "0.2"
          
        Finished using Selenium