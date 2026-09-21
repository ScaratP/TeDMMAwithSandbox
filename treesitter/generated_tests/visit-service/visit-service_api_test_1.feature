Feature: Visit Service API Tests

  Background:
    * url 'http://localhost:8080' 

  Scenario: Get sights by zone
    Given path 'sights'
    And param zone = 'north'
    When method get
    Then status 200
    And match response == [{ id: '#string', sightName: '#string', zone: 'north', category: '#string', photoURL: '#string', description: '#string', address: '#string' }]
  
  Scenario: Get sight by ID
    Given path 'sights/1'
    When method get
    Then status 200
    And match response == { id: '1', sightName: '#string', zone: '#string', category: '#string', photoURL: '#string', description: '#string', address: '#string' }

  Scenario: Get sight by non-existing ID
    Given path 'sights/999'
    When method get
    Then status 404

  Scenario: Get sights with invalid zone
    Given path 'sights'
    And param zone = 'invalid-zone'
    When method get
    Then status 400