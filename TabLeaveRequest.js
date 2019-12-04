import React from 'react';

import AvailableDaysCounter from './components/AvailableDaysCounter';
import LeaveRequestForm from './components/LeaveRequestForm';
import { QueryRenderer } from "react-relay";
import environment from "../../../../shared/relay/environment";
import graphql from "babel-plugin-relay/macro";

export const DaysAvailableContext = React.createContext(5);

const TabLeaveRequest = props => {

	return <QueryRenderer
		environment={props.environment || environment}
		query={graphql`
			query TabLeaveRequestQuery {
				reasons(tag: "vacation") {
					id 
					text
				}
				allocation {
					id 
					daysLeft 
					validFrom
					validUntil
					amount 
					reason 
					{ text }
				}
			}
		`}
		render={({ error, props, retry }) => {

			if (error) {
				return <div>{error.message}</div>
			} else if (props) {
				const {
					allocation: allocations
				} = props;

				const allocationTypes = [...new Set(allocations.map(allocation => allocation.reason.text))];

				const daysAvailableByType = [...allocationTypes.map(type =>
					({
						type: type,
						daysLeft: allocations
							.reduce((accumulator, item) => (
								item.reason.text === type ? accumulator + item.daysLeft : accumulator
							), 0)
					}))];

				//daysAvailableByType: Object with keys for each allocation type 
				return <div className="container container_sm tab-leave-request"
					data-testid="leave-request-form">
					<AvailableDaysCounter daysAvailableByType={daysAvailableByType} />
					<DaysAvailableContext.Provider value={daysAvailableByType} >
						<LeaveRequestForm data={props} />
					</DaysAvailableContext.Provider>
				</div>
			}

			return <div data-testid="leave-request-form">Loading</div>
		}}
	/>
};

export default TabLeaveRequest;
