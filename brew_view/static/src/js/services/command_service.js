
commandService.$inject = ['$http', '$rootScope'];

/**
 * commandService - Service for interacting with the command API.
 * @param  {$http} $http           Angular's $http Object.
 * @param  {$rootScope} $rootScope Angular's $rootScope Object.
 * @return {Object}               Service for interacting with the command API.
 */
export default function commandService($http, $rootScope) {
  return {
    getCommands: () => {
      return $http.get('api/v2/namespaces/{namespace}/commands');
    },
    getCommand: (id) => {
      return $http.get('api/v2/namespaces/{namespace}/commands/' + id);
    },
    findSystem: (command) => {
      return $rootScope.findSystemByID(command.system.id);
    },
    getStateParams: (command) => {
      let system = $rootScope.findSystemByID(command.system.id);
      return {
        systemName: system.name,
        systemVersion: $rootScope.getVersionForUrl(command.system),
        name: command.name,
        id: command.id,
      };
    },
  };
};
