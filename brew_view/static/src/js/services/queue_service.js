
queueService.$inject = ['$http'];

/**
 * queueService - Service for intereacting with the QueueAPI
 * @param  {Object} $http             Angular's $http Object.
 * @return {Object}                   Service for intereacting with the QueueAPI
 */
export default function queueService($http) {
  return {
    getQueues: () => {
      return $http.get('api/v2/namespaces/{namespace}/queues');
    },
    clearQueues: () => {
      return $http.delete('api/v2/namespaces/{namespace}/queues');
    },
    clearQueue: (name) => {
      return $http.delete('api/v2/namespaces/{namespace}/queues/'+name);
    },
  };
};
