Feature: log in

    Scenario: log in.feature 1. Test Invalid log in
        Using selenium
        Given I am not logged in
        When I access the url "/"
        Then I am at the log in page
        When I type "foo" for username
        When I type "foo" for password
        When I log in
        Then I am at the log in page
        Finished using Selenium
        
    Scenario: log in.feature 2. Test Student log in
        Using selenium
        Given I am not logged in
        When I access the url "/"
        Then I am at the log in page
        When I type "test_student_one" for username
        When I type "test" for password
        When I log in
        Then I am at the Home page
        When I log out
        Then I am at the Logged Out page
        Finished using Selenium      

    Scenario: log in.feature 3. Test Instructor log in
        Using selenium
        Given I am not logged in
        When I access the url "/"
        Then I am at the log in page
        When I type "test_instructor" for username
        When I type "test" for password
        When I log in
        Then I am at the Home page
        When I log out
        Then I am at the Logged Out page
        Finished using Selenium      