### [Service Identification]
- **Target Service**: pet-service

### [Artifacts: Karate API Testing]
- **File Name**: src/test/resources/pet-service/karate/pet-service.feature
- **Testing Code**:
```gherkin
Feature: Pet Service API

  Background:
    * url 'http://localhost:8080'

  Scenario: Get all pets
    Given path '/pets'
    When method get
    Then status 200
    And match response == []

  Scenario: Get pet by ID
    Given path '/pets/1'
    When method get
    Then status 200
    And match response == { id: 1, name: 'Buddy', birthDate: '2020-01-01', typeId: 1 }

  Scenario: Create a new pet
    Given path '/pets'
    And request { name: 'Max', birthDate: '2020-01-01', typeId: 1 }
    When method post
    Then status 201
    And match response == { id: '#number', name: 'Max', birthDate: '2020-01-01', typeId: 1 }

  Scenario: Update an existing pet
    Given path '/pets/1'
    And request { name: 'Buddy Updated', birthDate: '2020-01-01', typeId: 1 }
    When method put
    Then status 200
    And match response == { id: 1, name: 'Buddy Updated', birthDate: '2020-01-01', typeId: 1 }

  Scenario: Delete a pet
    Given path '/pets/1'
    When method delete
    Then status 204
```