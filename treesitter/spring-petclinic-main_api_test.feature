### [Service Identification]
- **Target Service**: sight-query-service

### [Artifacts: Karate API Testing]
- **File Name**: src/test/resources/sight-query-service/karate/sight-query.feature
- **Testing Code**:
```gherkin
Feature: Sight Query Service API

  Background:
    * url 'http://localhost:8080'

  Scenario: Get all sights by zone
    Given path '/sights'
    And param zone = 'North'
    When method GET
    Then status 200
    And match response == { id: '#string', sightName: '#string', zone: 'North', category: '#string', photoURL: '#string', description: '#string', address: '#string' }

  Scenario: Get sight by ID
    Given path '/sights/1'
    When method GET
    Then status 200
    And match response == { id: '1', sightName: 'Keelung Night Market', zone: 'North', category: 'Food', photoURL: 'http://example.com/photo.jpg', description: 'A vibrant night market.', address: 'No. 1, Keelung Rd, Keelung City' }
```