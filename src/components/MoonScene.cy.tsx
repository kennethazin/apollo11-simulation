import React from 'react'
import MoonScene from './MoonScene'

describe('<MoonScene />', () => {
  it('renders', () => {
    // see: https://on.cypress.io/mounting-react
    cy.mount(<MoonScene />)
  })
})