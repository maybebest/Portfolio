import React, { useMemo, useCallback, useRef } from 'react';

import { commitMutation } from 'react-relay';
import graphql from "babel-plugin-relay/macro"
import environment from "../../../../../../shared/relay/environment";

import Joi from '@hapi/joi';
import { Formik } from 'formik';
import { toast } from "react-toastify";

import LeaveRequestView from './LeaveRequestView';

import moment from 'moment';

const mutation = graphql`
    mutation LeaveRequestFormAddLeaveRequestMutation($input: LeaveRequestInput!) {
        addLeaveRequest(leaveRequest: $input) {
					leaveRequest {
						dateFrom
						dateTo
						willWorkOn
						comment
						allocation { id }
						reason { id }
					}
        }
    }
`;


export const sendMutation = (environment, onCompleted, onError, variables, resetFormCallback) => {
	commitMutation(environment, {
		mutation,
		onCompleted: (response, errors) => onCompleted(response, errors, resetFormCallback),
		onError: (error) => onError(error),
		variables
	});
};

const requestValidationSchema = Joi.object().keys({
	reason: Joi.number().error(() => "Reason must be selected"),
	allocation: Joi.number().error(() => "Allocation must be selected"),
	dateFrom: Joi.date().error(() => "Dates must be selected"),
	dateTo: Joi.date().error(() => "Dates must be selected"),
	comment: Joi.string().allow(''),
	willWorkOn: Joi.string().allow(''),
});


const LeaveRequestForm = ({
	data: {
		reasons: reasonsData,
		allocation: allocationsData,
	},
	handleDataReload
}) => {

	const initialValues = {
		dateFrom: '',
		dateTo: '',
		willWorkOn: '',
		comment: '',
		reason: reasonsData.length ? reasonsData[0].id : '',
		allocation: allocationsData.length ? allocationsData[0].id : '',
	};

	const allocations = useMemo(() => allocationsData.map(({
		id,
		reason: { text }
	}) => ({
		id: id,
		label: text,
		value: text
	})), [allocationsData]);

	const reasons = useMemo(() => reasonsData.map(({
		id,
		text
	}) => ({
		id: id,
		label: text,
		value: text
	})), [reasonsData]);

	const toastId = useRef(null);

	const showNotification = useCallback(() => toastId.current = toast("In progress, please wait...", {
		autoClose: true,
		closeButton: false,
		hideProgressBar: true,
	}), []);

	const onRequestExpenseSuccess = useCallback((response, errors, resetFormCallback) => {
		
		if (!errors) {
			toast.update(toastId.current, {
				render: 'Your request has been submitted',
				type: toast.TYPE.SUCCESS,
				autoClose: 3000,
				closeButton: true,
				hideProgressBar: false,
			});
		} else {
			toast.update(toastId.current, {
				render: 'Error during saving request',
				type: toast.TYPE.ERROR,
				autoClose: 3000,
				closeButton: true,
				hideProgressBar: false,
			});
		}
		if (errors) {
			return errors;
		}
		resetFormCallback();
		handleDataReload();
		return response;
	}, [toastId]);

	const onRequestExpenseError = useCallback((error) => {

		toast.update(toastId.current, {
			render: 'Error during saving request',
			type: toast.TYPE.ERROR,
			autoClose: 3000,
			closeButton: true,
			hideProgressBar: false,
		});
		return error;
	}, [toastId]);

	const handleRequestSubmit = useCallback((values, { resetForm, setSubmitting, setValues }) => {
		const variables = (({
			reason, allocation, dateTo, dateFrom, willWorkOn, comment
		}) => ({
			input: {
				comment,
				willWorkOn,
				dateFrom: moment(dateFrom).format('YYYY-MM-DD'),
				dateTo: moment(dateTo).format('YYYY-MM-DD'),
				reason: { id: reason },
				allocation: { id: allocation }
			},
		}))(values);

		showNotification();

		sendMutation(environment, onRequestExpenseSuccess, onRequestExpenseError, variables, resetForm);

		setSubmitting(false);
		setValues(initialValues);
	}, [onRequestExpenseError, onRequestExpenseSuccess, initialValues, showNotification]);

	const handleRequestValidation = useCallback(async (values) => {

		const validationResult = await Joi.validate(
			{
				...values,
			},
			requestValidationSchema,
			{
				abortEarly: false
			}
		);
		return validationResult.error;
	}, []);

	const renderFunction = useCallback(props => <LeaveRequestView
		formikProps={props}
		reasonsData={reasons}
		allocationsData={allocations}
	/>, [reasons, allocations]);

	return (
		<Formik
			initialValues={initialValues}
			onSubmit={handleRequestSubmit}
			validate={handleRequestValidation}
			validateOnChange={false}
			validateOnBlur={true}
			render={renderFunction}
		/>
	);
};

export default LeaveRequestForm;
