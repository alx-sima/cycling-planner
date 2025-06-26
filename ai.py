import matplotlib.pyplot as plt
import pickle as pkl
import sklearn as sk


class Model:
    def __init__(self, model: sk.base.BaseEstimator):
        self.model = model

    @staticmethod
    def create(**kwargs) -> "Model":
        model = sk.ensemble.RandomForestRegressor(**kwargs)
        return Model(model)

    @staticmethod
    def load(path: str) -> "Model":
        with open(path, "rb") as f:
            return Model(pkl.load(f))

    def save(self, path: str):
        with open(path, "wb") as f:
            pkl.dump(self.model, f)

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def score(self, X, y):
        return self.model.score(X, y)

    def display_stats(self, X_train, y_train, X_test, y_test):
        print("Feature importances:", self.model.feature_importances_)
        print(f"R^2 score on training set: {self.model.score(X_train, y_train):2f}")
        print(f"R^2 score on test set: {self.model.score(X_test, y_test):2f}")
        print(
            f"MAE on train set: {sk.metrics.mean_absolute_error(y_train, self.model.predict(X_train)):.2f}"
        )
        print(
            f"MSE on test set: {sk.metrics.mean_squared_error(y_test, self.model.predict(X_test)):.2f}"
        )

        plt.scatter(X_test[:, 0], y_test, label="Data")
        plt.plot(
            X_test[:, 0], self.model.predict(X_test), color="red", label="Prediction"
        )
        plt.xlabel("Incline (%)")
        plt.ylabel("Speed (km/h)")
        plt.legend()
        plt.show()
