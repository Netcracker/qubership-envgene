Feature: Template Inheritance (Template Composition)

  Scenario: UC-TI-PT-1: Build child template using a single parent template
    Given a child Template Repository is configured with parent-templates
    When the template build pipeline is executed
    Then the child template artifact inherits components from the basic-cloud parent

  Scenario: UC-TI-PT-2: Build child template composed from multiple parent templates
    Given a child Template Repository references multiple parent templates
    When the template build pipeline is executed
    Then the tenant and namespaces are composed from referenced parent templates
    And cloud and composite_structure are taken from child repository sources

  Scenario: UC-TI-CS-1: Use explicit composite_structure from child Template Descriptor
    Given the child Template Descriptor specifies composite_structure explicitly
    When the template build pipeline is executed
    Then the built artifact contains the explicit child composite_structure reference

  Scenario: UC-TI-OV-1: Override parent parameters for Cloud template
    Given a child Template Descriptor defines cloud.parent and overrides-parent section
    When the template build pipeline is executed
    Then the child Cloud template is inherited from parent and updated by overrides-parent

  Scenario: UC-TI-OV-2: Override parent parameters for Namespace template
    Given a child Template Descriptor defines a namespace with parent and overrides-parent section
    When the template build pipeline is executed
    Then the child Namespace template is inherited from parent and updated by overrides-parent
