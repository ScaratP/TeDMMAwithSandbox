Feature: Visit Service API

  Scenario: Get all visits
    Given url 'http://visit-service:8080/visits'
    When method get
    Then status 200
    And match response == '#array'

  Scenario: Get visit by ID
    Given url 'http://visit-service:8080/visits/1'
    When method get
    Then status 200
    And match response.id == 1
    And match response.date == '#string'
    And match response.description == '#string'

  Scenario: Create a new visit
    Given url 'http://visit-service:8080/visits'
    And request { "date": "2023-10-01", "description": "Check-up" }
    When method post
    Then status 201
    And match response.id == '#number'
    And match response.date == '2023-10-01'
    And match response.description == 'Check-up'

  Scenario: Update an existing visit
    Given url 'http://visit-service:8080/visits/1'
    And request { "date": "2023-10-02", "description": "Follow-up" }
    When method put
    Then status 200
    And match response.id == 1
    And match response.date == '2023-10-02'
    And match response.description == 'Follow-up'

  Scenario: Delete a visit
    Given url 'http://visit-service:8080/visits/1'
    When method delete
    Then status 204