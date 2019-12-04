import React from "react";

import { render, fireEvent, getByText, waitForElement, wait } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';

import TabLeaveRequest from '../src/screens/Vacations/components/TabLeaveRequest/TabLeaveRequest';

import { createMockEnvironment, MockPayloadGenerator } from 'relay-test-utils';

jest.mock('popper.js', () => class Popper {
  static placements = [
    'auto',
    'auto-end',
    'auto-start',
    'bottom',
    'bottom-end',
    'bottom-start',
    'left',
    'left-end',
    'left-start',
    'right',
    'right-end',
    'right-start',
    'top',
    'top-end',
    'top-start',
  ];

  constructor() {
    return {
      destroy: () => {
      },
      scheduleUpdate: () => {
      },
      disableEventListeners: () => {
      },
      update: () => {
      }
    };
  }
});

describe('<TabLeaveRequest/>', () => {

  it('Renders loading TabHistory', () => {
    const environment = createMockEnvironment();
    const { getByTestId } = render(<TabLeaveRequest environment={environment} />);

    expect(getByTestId('leave-request-form').textContent).toEqual('Loading');
  });

  it('<TabLeaveRequest/> renders with data', () => {
    const environment = createMockEnvironment();
    const { getByTestId } = render(<TabLeaveRequest environment={environment} />);

    environment.mock.resolveMostRecentOperation(operation =>
      MockPayloadGenerator.generate(operation, {
        ID(_, generateId) {
          return `${generateId()}`;
        },
        String(context) {
          if (context.name === "daysLeft") {
            return "8"
          }
          if (context.name === "text" && context.path.includes("reason") && context.path.includes("allocation")) {
            return "Medical expenses"
          }
          if (context.name === "text" && context.path.includes("reasons")) {
            return "Sick leave"
          }
          if (context.name === "amount") {
            return "10";
          }
        }
      }),
    );

    expect(getByTestId("leave-request-form")).toBeDefined();


  });

  it('<TabLeaveRequest/> has <AvailableDaysCounter/>', () => {
    const environment = createMockEnvironment();
    const { getByTestId } = render(<TabLeaveRequest environment={environment} />);

    environment.mock.resolveMostRecentOperation(operation =>
      MockPayloadGenerator.generate(operation, {
        ID(_, generateId) {
          return `${generateId()}`;
        },
        String(context) {
          if (context.name === "daysLeft") {
            return "8"
          }
          if (context.name === "text" && context.path.includes("reason") && context.path.includes("allocation")) {
            return "Medical expenses"
          }
          if (context.name === "text" && context.path.includes("reasons")) {
            return "Sick leave"
          }
          if (context.name === "amount") {
            return "10";
          }
        }
      }),
    );

    expect(getByTestId("available-days-counter")).toBeDefined();


  });

  it('<TabLeaveRequest/> has <AvailableDaysCounter/> with proper data', () => {
    const environment = createMockEnvironment();
    const { container } = render(<TabLeaveRequest environment={environment} />);

    environment.mock.resolveMostRecentOperation(operation =>
      MockPayloadGenerator.generate(operation, {
        ID(_, generateId) {
          return `${generateId()}`;
        },
        String(context) {
          if (context.name === "daysLeft") {
            return "8"
          }
          if (context.name === "text" && context.path.includes("reason") && context.path.includes("allocation")) {
            return "Medical expenses"
          }
          if (context.name === "text" && context.path.includes("reasons")) {
            return "Sick leave"
          }
          if (context.name === "amount") {
            return "10";
          }
        }
      }),
    );

    const allocationType = container.querySelector('span[class="available-days-counter__allocation-type"]').textContent;
    const daysAmount = container.querySelector('span[class="available-days-counter__days-amount"]').textContent;

    expect(allocationType).toEqual("Medical expenses");
    expect(daysAmount).toEqual("08 days");


  });

  it('<TabLeaveRequest/> shows allocations dropdown list with a proper allocation formatting', async () => {
    const environment = createMockEnvironment();
    const { container } = render(<TabLeaveRequest environment={environment} />);

    environment.mock.resolveMostRecentOperation(operation =>
      MockPayloadGenerator.generate(operation, {
        ID(_, generateId) {
          return `${generateId()}`;
        },
        String(context) {
          if (context.name === "daysLeft") {
            return "8"
          }
          if (context.name === "validUntil") {
            return "2019-10-25"
          }
          if (context.name === "validFrom") {
            return "2019-10-25"
          }
          if (context.name === "text" && context.path.includes("reason") && context.path.includes("allocation")) {
            return "Medical expenses"
          }
          if (context.name === "text" && context.path.includes("reasons")) {
            return "Sick leave"
          }
          if (context.name === "amount") {
            return "10";
          }
        }
      }),
    );
    await wait();

    expect(container.querySelectorAll('.input-group__single-value')[1].textContent).toEqual('Medical expenses (8 days until October 25 · 2019)');
  });

  it('<TabLeaveRequest/> shows allocations dropdown list with a proper allocation formatting', async () => {
    const environment = createMockEnvironment();
    const { asFragment } = render(<TabLeaveRequest environment={environment} />);

    environment.mock.resolveMostRecentOperation(operation =>
      MockPayloadGenerator.generate(operation, {
        ID(_, generateId) {
          return `${generateId()}`;
        },
        String(context) {
          if (context.name === "daysLeft") {
            return "8"
          }
          if (context.name === "validUntil") {
            return "2019-10-25"
          }
          if (context.name === "validFrom") {
            return "2019-10-25"
          }
          if (context.name === "text" && context.path.includes("reason") && context.path.includes("allocation")) {
            return "Medical expenses"
          }
          if (context.name === "text" && context.path.includes("reasons")) {
            return "Sick leave"
          }
          if (context.name === "amount") {
            return "10";
          }
        }
      }),
    );

    expect(asFragment()).toMatchSnapshot();
  });

});
