
instanceService.$inject = ['$http'];

/**
 * instanceService - Service for interacting with the instance API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Service for interacting with the instance API.
 */
export default function instanceService($http) {
  return {
    startInstance: (instance) => {
      return $http.patch(
        'api/v2/namespaces/{namespace}/instances/' + instance.id,
        {operation: 'start'},
      );
    },
    stopInstance: (instance) => {
      return $http.patch(
        'api/v2/namespaces/{namespace}/instances/' + instance.id,
        {operation: 'stop'},
      );
    },
  };
};
